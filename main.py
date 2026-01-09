from mcp.server.fastmcp import FastMCP
import nbformat
import re
from typing import Optional, List

mcp = FastMCP(
    "notebook",
    dependencies=["nbformat"]
)

# =========================
# Utilities (from hello.py)
# =========================

def normalize_text(x):
    if isinstance(x, list):
        return "".join(x)
    return x or ""

def format_outputs(outputs):
    lines = []
    has_error = False
    for out in outputs:
        otype = out.output_type
        if otype == "stream":
            text = normalize_text(out.text).strip()
            if text:
                lines.append(text)
        elif otype in ("execute_result", "display_data"):
            data = out.data or {}
            if "text/plain" in data:
                lines.append(str(data["text/plain"]).strip())
        elif otype == "error":
            has_error = True
            lines.append("ERROR:")
            lines.append(f"{out.ename}: {out.evalue}")
            lines.extend(out.traceback)
    return "\n".join(lines), has_error

def format_cell(cell, index):
    source = normalize_text(cell.source).strip()
    if cell.cell_type == "markdown":
        return f"\n[CELL {index} | MARKDOWN]\n{source}\n"
    if cell.cell_type == "code":
        output_text, has_error = format_outputs(cell.outputs)
        execution_count = cell.execution_count
        return (
            f"\n[CELL {index} | CODE]\n"
            f"[EXECUTION_COUNT] {execution_count}\n"
            f"[HAS_ERROR] {has_error}\n\n"
            f"{source}\n\n"
            f"[OUTPUT]\n"
            f"{output_text if output_text else '<NO OUTPUT>'}\n"
        )
    return ""

def notebook_to_llm_blocks(notebook_path):
    nb = nbformat.read(notebook_path, as_version=4)
    blocks = []
    for i, cell in enumerate(nb.cells):
        block = format_cell(cell, i)
        if block.strip():
            blocks.append(block)
    return blocks

# =========================
# Filters (from hello.py)
# =========================

def filter_by_keyword(blocks, keywords):
    if isinstance(keywords, str):
        keywords = [keywords]
    result = []
    for block in blocks:
        text = block.lower()
        if any(k.lower() in text for k in keywords):
            result.append(block)
    return result

def filter_by_cell_index(blocks, start=None, end=None):
    result = []
    for block in blocks:
        header = block.split("\n", 1)[0]
        if not header.startswith("[CELL"):
            continue
        idx = int(header.split("[CELL")[1].split("|")[0].strip())
        if start is not None and idx < start:
            continue
        if end is not None and idx >= end:
            continue
        result.append(block)
    return result

def filter_has_error(blocks, has_error=True):
    result = []
    for block in blocks:
        for line in block.splitlines():
            if line.startswith("[HAS_ERROR]"):
                flag = line.split("]", 1)[1].strip().lower() == "true"
                if flag == has_error:
                    result.append(block)
                break
    return result

# =========================
# MCP Tool
# =========================

@mcp.tool()
def read_notebook(
    path: str,
    keywords: Optional[List[str]] = None,
    start_cell: Optional[int] = None,
    end_cell: Optional[int] = None,
    only_errors: Optional[bool] = None
) -> str:
    """
    Reads a Jupyter Notebook (.ipynb) and returns a formatted text representation for LLM analysis.
    Filters are optional and can be combined.
    
    Args:
        path: Path to the .ipynb file.
        keywords: List of keywords to filter cells (e.g., ["fit", "model"]).
        start_cell: Start cell index (inclusive).
        end_cell: End cell index (exclusive).
        only_errors: If True, only returns cells that have execution errors.
    """
    try:
        blocks = notebook_to_llm_blocks(path)
        
        if keywords:
            blocks = filter_by_keyword(blocks, keywords)
        
        if start_cell is not None or end_cell is not None:
            blocks = filter_by_cell_index(blocks, start=start_cell, end=end_cell)
            
        if only_errors is not None:
            blocks = filter_has_error(blocks, has_error=only_errors)
            
        if not blocks:
            return "No matching cells found with the specified filters."
            
        return "\n".join(blocks)
    except Exception as e:
        return f"Error reading notebook: {str(e)}"

if __name__ == "__main__":
    mcp.run()
