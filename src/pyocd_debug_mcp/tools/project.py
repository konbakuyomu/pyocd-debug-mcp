"""Project configuration management for pyocd-debug-mcp.

Provides .pyocd-debug.json config file support:
- load_project(): read config or auto-discover debug files
- init_project(): create config file from explicit paths or scan results
- scan_project_files(): recursively find .hex/.axf/.elf/.svd in project dir
- find_builtin_svd(): check pyocd's built-in svd_data.zip for fallback SVD
"""

import json
import os
import zipfile
import tempfile
from pathlib import Path

CONFIG_FILENAME = ".pyocd-debug.json"

SKIP_DIRS = {
    ".git", ".venv", ".env", "node_modules", "__pycache__",
    ".vscode", ".settings", ".cache", ".mypy_cache", ".cmsis",
}

FIRMWARE_EXTS = {".hex", ".bin"}
ELF_EXTS = {".elf", ".axf"}
SVD_EXTS = {".svd"}

MAX_SCAN_DEPTH = 5

# Cache for pyocd built-in SVD listing (loaded once)
_builtin_svd_cache: dict[str, str] | None = None


def _list_builtin_svd() -> dict[str, str]:
    """Return {lowercase_name: original_name} of pyocd's built-in SVD files."""
    global _builtin_svd_cache
    if _builtin_svd_cache is not None:
        return _builtin_svd_cache

    _builtin_svd_cache = {}
    try:
        import importlib_resources
    except ImportError:
        try:
            import importlib.resources as importlib_resources
        except ImportError:
            return _builtin_svd_cache

    try:
        zip_ref = importlib_resources.files("pyocd").joinpath(
            "debug/svd/svd_data.zip"
        )
        with zip_ref.open("rb") as f:
            z = zipfile.ZipFile(f)
            for name in z.namelist():
                _builtin_svd_cache[name.lower()] = name
    except Exception:
        pass
    return _builtin_svd_cache


def find_builtin_svd(target_type: str) -> dict | None:
    """Try to find a matching SVD in pyocd's built-in svd_data.zip.

    Matching strategy:
    1. Exact: target_type → strip trailing variant (hc32f4a0xi → HC32F4A0)
    2. Prefix: find any built-in SVD whose name starts with the base chip name

    Returns dict with svd_builtin_name, warning, and extraction info,
    or None if no match found.
    """
    builtin = _list_builtin_svd()
    if not builtin:
        return None

    # Extract base chip name: strip trailing variant letters
    # hc32f4a0xi → hc32f4a0, stm32f407xe → stm32f407, nrf52840 → nrf52840
    base = target_type.lower()
    # pyocd target names often end with 1-2 variant chars after the chip family
    # Try progressively shorter prefixes
    candidates = []
    for bname, original in builtin.items():
        stem = os.path.splitext(bname)[0]
        if stem == base or base.startswith(stem) or stem.startswith(base):
            candidates.append(original)

    if not candidates:
        # Try with common suffixes stripped
        for suffix_len in range(1, 4):
            if len(base) <= suffix_len:
                break
            prefix = base[:-suffix_len]
            for bname, original in builtin.items():
                stem = os.path.splitext(bname)[0]
                if stem.lower().startswith(prefix):
                    if original not in candidates:
                        candidates.append(original)
            if candidates:
                break

    if not candidates:
        return None

    return {
        "svd_builtin_names": candidates,
        "_svd_builtin_warning": (
            "⚠️ pyocd 内置 SVD 通常是通用版本，可能缺少特定封装的引脚映射和外设变体。"
            "强烈建议从芯片厂商 SDK 或 CMSIS-Pack 中获取与您具体芯片型号匹配的 SVD 文件，"
            "并通过 pyocd_project_init() 写入 .pyocd-debug.json 配置。"
        ),
    }


def extract_builtin_svd(svd_name: str, output_dir: str) -> str | None:
    """Extract a specific SVD from pyocd's built-in svd_data.zip.

    Returns absolute path to extracted file, or None on failure.
    """
    try:
        import importlib_resources
    except ImportError:
        try:
            import importlib.resources as importlib_resources
        except ImportError:
            return None

    try:
        zip_ref = importlib_resources.files("pyocd").joinpath(
            "debug/svd/svd_data.zip"
        )
        with zip_ref.open("rb") as f:
            z = zipfile.ZipFile(f)
            svd_data = z.read(svd_name)

        out_path = os.path.join(output_dir, svd_name)
        with open(out_path, "wb") as out:
            out.write(svd_data)
        return out_path
    except Exception:
        return None


def scan_project_files(project_path: Path) -> dict:
    """Recursively scan for debug-related files."""
    result: dict[str, list[str]] = {
        "firmware_candidates": [],
        "elf_candidates": [],
        "svd_candidates": [],
    }

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        depth = len(Path(root).relative_to(project_path).parts)
        if depth > MAX_SCAN_DEPTH:
            dirs.clear()
            continue

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in FIRMWARE_EXTS and ext not in ELF_EXTS and ext not in SVD_EXTS:
                continue

            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, project_path).replace("\\", "/")

            if ext in FIRMWARE_EXTS:
                result["firmware_candidates"].append(rel)
            elif ext in ELF_EXTS:
                result["elf_candidates"].append(rel)
            elif ext in SVD_EXTS:
                result["svd_candidates"].append(rel)

    return result


def load_project(project_dir: str) -> dict:
    """Load project config or auto-discover debug files.

    Returns config dict with _source indicating origin.
    If config file missing, returns auto-discovered candidates
    with a suggestion to create the config.
    """
    project_path = Path(project_dir)
    if not project_path.is_dir():
        return {"error": f"Directory not found: {project_dir}"}

    config_path = project_path / CONFIG_FILENAME

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            return {"error": f"Failed to parse {config_path}: {e}"}

        config["_source"] = "config_file"
        config["_config_path"] = str(config_path)

        # Resolve relative paths to absolute
        resolved = {}
        for key in ("firmware", "elf", "svd"):
            val = config.get(key)
            if val and not os.path.isabs(val):
                abs_path = str(project_path / val)
                resolved[key] = abs_path
                config[key] = abs_path

        # Validate that files exist
        missing = []
        for key in ("firmware", "elf", "svd"):
            val = config.get(key)
            if val and not os.path.isfile(val):
                missing.append(f"{key}: {val}")
        if missing:
            config["_missing_files"] = missing

        # SVD fallback: if no SVD in config, try pyocd built-in
        if not config.get("svd"):
            target_type = config.get("target", "")
            if target_type:
                fallback = find_builtin_svd(target_type)
                if fallback:
                    config["_svd_fallback"] = fallback
                    config["_svd_recommendation"] = (
                        "配置中未指定 SVD 文件。发现 pyocd 内置 SVD 可作为临时回退，"
                        "但强烈建议在 .pyocd-debug.json 中指定芯片厂商提供的完整 SVD 文件。"
                        "内置 SVD 通常是通用简化版，可能缺少部分外设定义或封装特定引脚。"
                    )

        return config

    # No config file — auto-discover
    discovered = scan_project_files(project_path)
    discovered["_source"] = "auto_discovered"
    discovered["_config_missing"] = True
    discovered["_project_dir"] = project_dir
    discovered["_suggestion"] = (
        f"No {CONFIG_FILENAME} found in {project_dir}. "
        f"Use pyocd_project_init() to create one for reliable debugging. "
        f"Auto-discovered file candidates are listed below — "
        f"pass the correct ones to pyocd_project_init()."
    )

    # If no SVD found in project scan, check pyocd built-in as last resort
    if not discovered.get("svd_candidates"):
        discovered["_svd_recommendation"] = (
            "项目目录中未发现 SVD 文件。请从芯片厂商 SDK 或官网下载对应型号的 SVD 文件，"
            "放入项目目录并通过 pyocd_project_init(svd=...) 指定。"
            "pyocd 内置有部分通用 SVD 可临时使用（通过 pyocd_svd_attach_builtin），"
            "但内置版本可能不完整，强烈建议使用厂商提供的完整版本。"
        )
        # Try to provide built-in candidates (need target hint)
        discovered["_svd_builtin_available"] = len(_list_builtin_svd())

    return discovered


def init_project(
    project_dir: str,
    target: str,
    firmware: str | None = None,
    elf: str | None = None,
    svd: str | None = None,
    probe: str | None = None,
) -> dict:
    """Create .pyocd-debug.json in project directory.

    Converts absolute paths under project_dir to relative paths.
    """
    project_path = Path(project_dir)
    if not project_path.is_dir():
        return {"error": f"Directory not found: {project_dir}"}

    config: dict = {"target": target}

    for key, value in [("firmware", firmware), ("elf", elf),
                       ("svd", svd), ("probe", probe)]:
        if not value:
            continue
        if key == "probe":
            config[key] = value
            continue
        # Convert to relative path if under project dir
        try:
            rel = os.path.relpath(value, project_dir)
            if not rel.startswith(".."):
                config[key] = rel.replace("\\", "/")
            else:
                config[key] = value.replace("\\", "/")
        except ValueError:
            config[key] = value.replace("\\", "/")

    config_path = project_path / CONFIG_FILENAME
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return {
        "status": "created",
        "config_path": str(config_path),
        "config": config,
    }
