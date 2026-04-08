"""Project configuration management for pyocd-debug-mcp.

Provides .pyocd-debug.json config file support:
- load_project(): read config or auto-discover debug files
- init_project(): create config file from explicit paths or scan results
- scan_project_files(): recursively find .hex/.axf/.elf/.svd in project dir
"""

import json
import os
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
