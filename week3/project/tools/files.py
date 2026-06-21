import os
import fnmatch

WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", ".")

def resolve_path(path: str) -> str:
    abs_root = os.path.abspath(WORKSPACE_ROOT)
    abs_target = os.path.abspath(os.path.join(abs_root, path))
    if not abs_target.startswith(abs_root):
        raise PermissionError("Path escapes workspace sandbox security limits.")
    return abs_target

def read_file(path: str, start_line: int = 1, read_lines: int = 200) -> dict:
    try:
        target = resolve_path(path)
        if not os.path.exists(target):
            return {"error": f"File not found: {path}"}
        
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, start_idx + read_lines)
        
        content_lines = []
        for idx in range(start_idx, end_idx):
            content_lines.append(f"{idx + 1}| {lines[idx].rstrip()}")
            
        has_more = end_idx < total_lines
        return {
            "content": "\n".join(content_lines),
            "metadata": {"total_lines": total_lines, "has_more": has_more}
        }
    except Exception as e:
        return {"error": str(e)}

def write_file(path: str, content: str) -> dict:
    try:
        target = resolve_path(path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success", "written_bytes": len(content)}
    except Exception as e:
        return {"error": str(e)}

def list_files(pattern: str = "*") -> dict:
    try:
        root = os.path.abspath(WORKSPACE_ROOT)
        matched_files = []
        for base, dirs, files in os.walk(root):
            for file in files:
                full_path = os.path.join(base, file)
                rel_path = os.path.relpath(full_path, root)
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(file, pattern):
                    matched_files.append(rel_path)
        return {"files": matched_files}
    except Exception as e:
        return {"error": str(e)}

def edit_file(path: str, operation: str, start_line: int, end_line: int = None, content: str = "") -> dict:
    try:
        target = resolve_path(path)
        if not os.path.exists(target):
            return {"error": f"File not found for editing: {path}"}
            
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        new_content_lines = [line + "\n" for line in content.splitlines()] if content else []
        s_idx = max(0, start_line - 1)
        e_idx = max(s_idx, end_line - 1) if end_line is not None else s_idx
        
        orig_preview = "".join(lines[s_idx:e_idx+1])
        
        if operation == "replace":
            lines[s_idx:e_idx+1] = new_content_lines
        elif operation == "delete":
            lines[s_idx:e_idx+1] = []
        elif operation == "append":
            lines[s_idx+1:s_idx+1] = new_content_lines
        else:
            return {"error": f"Unknown operation: {operation}"}
            
        with open(target, "w", encoding="utf-8") as f:
            f.writelines(lines)
            
        return {
            "status": "success",
            "operation": operation,
            "preview_diff": {
                "before": orig_preview.rstrip(),
                "after": content.rstrip() if operation != "delete" else ""
            }
        }
    except Exception as e:
        return {"error": str(e)}