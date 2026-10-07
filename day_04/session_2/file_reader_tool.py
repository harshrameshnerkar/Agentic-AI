"""
file_reader_tool.py
===================
Tool 2 of 4: Safe File Reader Tool (Day 4 - Session 2)

Design Best Practices Implemented:
1. Clear Naming: 'read_file' states exact functionality.
2. Security & Sandboxing: Restricts reads to authorized directories, preventing directory traversal.
3. Pagination & Token Overload Guard:
   - Provides 'start_line' and 'max_lines' to prevent dumping massive files into LLM context.
4. Error as Observation:
   - File not found? Returns file list of directory so agent can correct filename.
   - Access denied? Returns clear security observation.
   - Is a directory? Informs agent to pick a specific file.
"""

from pathlib import Path
from typing import Dict, Any, Optional

# Authorized sandbox root: Defaults to current session directory or workspace
DEFAULT_SANDBOX_DIR = Path(__file__).parent.resolve()


def read_file(
    file_path: str,
    max_lines: int = 150,
    start_line: int = 1,
    sandbox_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Safely reads text content from a file within the authorized workspace.

    Args:
        file_path: Relative or absolute path to the file to read.
        max_lines: Maximum number of lines to return (1 to 500). Defaults to 150.
        start_line: 1-indexed line number to start reading from. Defaults to 1.
        sandbox_dir: Optional override for the root allowed directory.
    """
    root_dir = (sandbox_dir or DEFAULT_SANDBOX_DIR).resolve()

    # 1. Argument Validation
    if not isinstance(file_path, str) or not file_path.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'file_path' argument must be a non-empty string.",
        }

    try:
        start_line = max(1, int(start_line))
        max_lines = min(max(1, int(max_lines)), 500)
    except (ValueError, TypeError):
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "Arguments 'start_line' and 'max_lines' must be valid integers.",
        }

    # 2. Path Resolution & Sandbox Enforcement
    target_path = Path(file_path)
    if not target_path.is_absolute():
        target_path = (root_dir / target_path).resolve()
    else:
        target_path = target_path.resolve()

    # Security check: Ensure path does not escape sandbox
    try:
        target_path.relative_to(root_dir)
    except ValueError:
        return {
            "status": "error",
            "error_type": "SecurityError",
            "message": (
                f"Access Denied: The requested path '{file_path}' resolves outside "
                f"the authorized workspace directory '{root_dir}'. Path traversal is forbidden."
            ),
        }

    # 3. Path Existence & Type Checks
    if not target_path.exists():
        # Help the model self-correct by listing neighboring files
        parent_dir = target_path.parent if target_path.parent.exists() else root_dir
        sibling_files = [f.name for f in parent_dir.iterdir() if f.is_file()][:10]

        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"File '{file_path}' was not found.",
            "suggestion": f"Check the filename spelling. Files in '{parent_dir.name}': {sibling_files}",
        }

    if target_path.is_dir():
        child_files = [f.name for f in target_path.iterdir() if f.is_file()][:10]
        return {
            "status": "error",
            "error_type": "IsADirectoryError",
            "message": f"'{file_path}' is a directory, not a file.",
            "available_files": child_files,
        }

    # 4. Safe Read with Encoding Handling
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return {
            "status": "error",
            "error_type": "BinaryFileError",
            "message": f"File '{file_path}' contains binary data and cannot be read as UTF-8 text.",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "IOError",
            "message": f"Failed to read file '{file_path}': {str(e)}",
        }

    total_lines = len(lines)
    # Apply slice: 1-indexed to 0-indexed
    start_idx = start_line - 1
    end_idx = min(start_idx + max_lines, total_lines)
    selected_lines = lines[start_idx:end_idx]

    content_snippet = "".join(selected_lines)
    is_truncated = end_idx < total_lines

    return {
        "status": "success",
        "file_path": str(target_path.relative_to(root_dir)),
        "start_line": start_line,
        "lines_returned": len(selected_lines),
        "total_lines": total_lines,
        "is_truncated": is_truncated,
        "content": content_snippet,
    }


if __name__ == "__main__":
    print("=== Testing read_file Tool ===")
    
    # 1. Read existing file
    readme_res = read_file("requirements.txt")
    print("Read 'requirements.txt':", readme_res["status"], f"({readme_res.get('lines_returned')} lines)")

    # 2. File not found with suggestion
    missing_res = read_file("non_existent_config.json")
    print("Missing file (Observation):", missing_res["error_type"], "-", missing_res["suggestion"])

    # 3. Path traversal attack blocked
    traversal_res = read_file("../../windows/system32/cmd.exe")
    print("Security Traversal Block (Observation):", traversal_res["error_type"], "-", traversal_res["message"][:70])
