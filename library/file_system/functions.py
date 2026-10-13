
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

import config


def _configured_root() -> Path:
    configured = getattr(config, "FILE_SYSTEM_ROOT", None)
    if not configured or not str(configured).strip():
        raise RuntimeError(
            "Set FILE_SYSTEM_ROOT in config.py, for example "
            r'''FILE_SYSTEM_ROOT = r"D:\Projects\test"'''
        )

    root = Path(str(configured)).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(
            f"Configured file-system root does not exist: {root}. "
            "Create this folder first, or correct FILE_SYSTEM_ROOT."
        )
    if not root.is_dir():
        raise NotADirectoryError(f"FILE_SYSTEM_ROOT is not a folder: {root}")
    return root


def _safe_path(path: str = ".", *, allow_root: bool = True) -> Path:
    """Resolve a user path and reject any path outside the configured root."""
    if not isinstance(path, str):
        raise TypeError("Path must be a string.")
    if "\x00" in path:
        raise ValueError("Path contains an invalid null character.")

    root = _configured_root()
    supplied = Path(path).expanduser()

    # Absolute paths are accepted only if their resolved destination stays
    # inside the configured root. Relative paths are interpreted under root.
    candidate = supplied if supplied.is_absolute() else root / supplied
    resolved = candidate.resolve()

    try:
        resolved.relative_to(root)
    except ValueError:
        raise PermissionError(
            f"Access denied: paths must stay inside the configured folder ({root})."
        ) from None

    if not allow_root and resolved == root:
        raise PermissionError("This operation cannot target the configured root folder.")
    return resolved


def _safe_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name cannot be empty.")
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("Use a simple item name, not a path.")
    if "\x00" in name:
        raise ValueError("Name contains an invalid null character.")
    return name


def list_directory(path: str = ".") -> list:
    """List files and folders directly inside a directory."""
    folder = _safe_path(path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {path}")
    items = []
    for item in sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold())):
        # Do not expose a symlink target outside the root.
        try:
            safe_item = _safe_path(str(item))
        except (PermissionError, OSError):
            continue
        stat = safe_item.stat()
        items.append({
            "name": item.name,
            "type": "folder" if safe_item.is_dir() else "file",
            "path": str(safe_item.relative_to(_configured_root())),
            "size_bytes": stat.st_size if safe_item.is_file() else None,
        })
    return items


def create_file(path: str, content: str = "", overwrite: bool = False) -> str:
    """Create a file within the configured root."""
    target = _safe_path(path, allow_root=False)
    if target.exists() and target.is_dir():
        raise IsADirectoryError(f"A folder already exists at: {path}")
    if target.exists() and not overwrite:
        raise FileExistsError(f"Item already exists: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"File created: {target.relative_to(_configured_root())}"


def read_file(path: str, max_bytes: int = 1_000_000) -> str:
    """Read a UTF-8 text file, with a size limit."""
    target = _safe_path(path, allow_root=False)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer.")
    if target.stat().st_size > max_bytes:
        raise ValueError(f"File is larger than the read limit ({max_bytes} bytes).")
    return target.read_text(encoding="utf-8")


def append_file(path: str, content: str) -> str:
    """Append text to an existing UTF-8 file."""
    target = _safe_path(path, allow_root=False)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    with target.open("a", encoding="utf-8", newline="") as file:
        file.write(content)
    return f"Text appended to: {target.relative_to(_configured_root())}"


def create_folder(path: str) -> str:
    """Create a folder within the configured root."""
    target = _safe_path(path, allow_root=False)
    target.mkdir(parents=True, exist_ok=False)
    return f"Folder created: {target.relative_to(_configured_root())}"


def delete_file(path: str) -> str:
    """Delete one file. The execution environment should require confirmation."""
    target = _safe_path(path, allow_root=False)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    target.unlink()
    return f"File deleted: {target.relative_to(_configured_root())}"


def delete_folder(path: str) -> str:
    """Recursively delete a folder. The execution environment should require confirmation."""
    import shutil

    target = _safe_path(path, allow_root=False)
    if not target.is_dir():
        raise NotADirectoryError(f"Folder not found: {path}")
    shutil.rmtree(target)
    return f"Folder and its contents deleted: {target.relative_to(_configured_root())}"


def rename_item(path: str, new_name: str) -> str:
    """Rename a file or folder without leaving the configured root."""
    target = _safe_path(path, allow_root=False)
    name = _safe_name(new_name)
    if not target.exists():
        raise FileNotFoundError(f"Item not found: {path}")
    destination = _safe_path(str(target.parent / name), allow_root=False)
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {new_name}")
    target.rename(destination)
    return f"Renamed '{target.name}' to '{destination.name}'."


def move_item(path: str, destination_folder: str) -> str:
    """Move a file or folder to another folder inside the configured root."""
    import shutil

    source = _safe_path(path, allow_root=False)
    destination_dir = _safe_path(destination_folder)
    if not source.exists():
        raise FileNotFoundError(f"Item not found: {path}")
    if not destination_dir.is_dir():
        raise NotADirectoryError(f"Destination folder not found: {destination_folder}")
    destination = _safe_path(str(destination_dir / source.name), allow_root=False)
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination.name}")
    shutil.move(str(source), str(destination))
    return f"Moved '{source.name}' to '{destination_dir.relative_to(_configured_root())}'."


def find_file(name: str, start_path: str = ".") -> list:
    """Find files by exact name or case-insensitive partial name."""
    folder = _safe_path(start_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {start_path}")
    query = name.casefold()
    matches = []
    for current, dirs, files in os.walk(folder, followlinks=False):
        current_path = Path(current)
        # Prune symlink directories and any directory that resolves outside root.
        safe_dirs = []
        for dirname in dirs:
            candidate = current_path / dirname
            try:
                _safe_path(str(candidate))
                if not candidate.is_symlink():
                    safe_dirs.append(dirname)
            except (PermissionError, OSError):
                pass
        dirs[:] = safe_dirs
        for filename in files:
            candidate = current_path / filename
            if query in filename.casefold():
                try:
                    safe = _safe_path(str(candidate))
                except (PermissionError, OSError):
                    continue
                if safe.is_file():
                    matches.append(str(safe.relative_to(_configured_root())))
    return matches


def find_folder(name: str, start_path: str = ".") -> list:
    """Find folders by exact name or case-insensitive partial name."""
    folder = _safe_path(start_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {start_path}")
    query = name.casefold()
    matches = []
    for current, dirs, _files in os.walk(folder, followlinks=False):
        current_path = Path(current)
        safe_dirs = []
        for dirname in dirs:
            candidate = current_path / dirname
            try:
                safe = _safe_path(str(candidate))
                if candidate.is_symlink():
                    continue
            except (PermissionError, OSError):
                continue
            safe_dirs.append(dirname)
            if query in dirname.casefold() and safe.is_dir():
                matches.append(str(safe.relative_to(_configured_root())))
        dirs[:] = safe_dirs
    return matches


def get_item_info(path: str) -> dict:
    """Return basic information about a file or folder."""
    target = _safe_path(path, allow_root=False)
    if not target.exists():
        raise FileNotFoundError(f"Item not found: {path}")
    stat = target.stat()
    return {
        "name": target.name,
        "type": "folder" if target.is_dir() else "file",
        "relative_path": str(target.relative_to(_configured_root())),
        "size_bytes": stat.st_size if target.is_file() else None,
        "modified_time": __import__("datetime").datetime.fromtimestamp(
            stat.st_mtime
        ).isoformat(timespec="seconds"),
    }


def open_file(path: str) -> str:
    """Open a file using its Windows default application."""
    target = _safe_path(path, allow_root=False)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    if platform.system() != "Windows":
        raise OSError("open_file currently supports Windows only.")
    os.startfile(str(target))
    return f"Opened file: {target.relative_to(_configured_root())}"


def open_folder(path: str = ".") -> str:
    """Open a folder in Windows File Explorer."""
    target = _safe_path(path)
    if not target.is_dir():
        raise NotADirectoryError(f"Folder not found: {path}")
    if platform.system() != "Windows":
        raise OSError("open_folder currently supports Windows only.")
    os.startfile(str(target))
    return f"Opened folder: {target.relative_to(_configured_root()) or '.'}"


def _entry(name, function, parameters=(), required=(), defaults=None,
           processing="Processing file-system request...",
           speak_text="Working on request...",
           response="Completed: {result}", risk_level="low",
           confirmation_required=False):
    return {
        "name": name,
        "function": function,
        "parameters": list(parameters),
        "required": list(required),
        "defaults": dict(defaults or {}),
        "category": "filesystem",
        "risk_level": risk_level,
        "confirmation_required": confirmation_required,
        "processing_command": processing,
        "speak": speak_text,
        "response": response,
    }


FUNCTIONS = [
    _entry("list_directory", list_directory, ["path"], defaults={"path": "."},
           processing="Listing folder items...", response="Folder items: {result}"),
    _entry("create_file", create_file, ["path", "content", "overwrite"], ["path"],
           defaults={"content": "", "overwrite": False},
           processing="Creating file...", response="{result}"),
    _entry("read_file", read_file, ["path", "max_bytes"], ["path"],
           defaults={"max_bytes": 1000000},
           processing="Reading file...", response="File content: {result}"),
    _entry("append_file", append_file, ["path", "content"], ["path", "content"],
           processing="Appending to file...", response="{result}"),
    _entry("create_folder", create_folder, ["path"], ["path"],
           processing="Creating folder...", response="{result}"),
    _entry("delete_file", delete_file, ["path"], ["path"],
           processing="Deleting file...", response="{result}",
           risk_level="high", confirmation_required=True),
    _entry("delete_folder", delete_folder, ["path"], ["path"],
           processing="Deleting folder and its contents...", response="{result}",
           risk_level="critical", confirmation_required=True),
    _entry("rename_item", rename_item, ["path", "new_name"], ["path", "new_name"],
           processing="Renaming item...", response="{result}"),
    _entry("move_item", move_item, ["path", "destination_folder"],
           ["path", "destination_folder"],
           processing="Moving item...", response="{result}"),
    _entry("find_file", find_file, ["name", "start_path"], ["name"],
           defaults={"start_path": "."},
           processing="Searching for files...", response="Matching files: {result}"),
    _entry("find_folder", find_folder, ["name", "start_path"], ["name"],
           defaults={"start_path": "."},
           processing="Searching for folders...", response="Matching folders: {result}"),
    _entry("get_item_info", get_item_info, ["path"], ["path"],
           processing="Reading item details...", response="Item details: {result}"),
    _entry("open_file", open_file, ["path"], ["path"],
           processing="Opening file...", response="{result}"),
    _entry("open_folder", open_folder, ["path"], defaults={"path": "."},
           processing="Opening folder in File Explorer...", response="{result}"),
]

