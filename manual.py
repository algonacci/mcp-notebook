import nbformat
import re


# =========================
# Utilities
# =========================

def normalize_text(x):
    if isinstance(x, list):
        return "".join(x)
    return x or ""


# =========================
# Output Formatting
# =========================

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


# =========================
# Cell Formatting
# =========================

def format_cell(cell, index):
    source = normalize_text(cell.source).strip()

    # Markdown cell
    if cell.cell_type == "markdown":
        return (
            f"\n[CELL {index} | MARKDOWN]\n"
            f"{source}\n"
        )

    # Code cell
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


# =========================
# Notebook Parsing
# =========================

def notebook_to_llm_blocks(notebook_path):
    nb = nbformat.read(notebook_path, as_version=4)

    blocks = []
    for i, cell in enumerate(nb.cells):
        block = format_cell(cell, i)
        if block.strip():
            blocks.append(block)

    return blocks


# =========================
# Filters
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
# Function → Cell Mapping
# =========================

def build_function_cell_map(blocks):
    func_map = {}
    pattern = re.compile(r"^\s*def\s+([a-zA-Z_]\w*)\s*\(", re.MULTILINE)

    for block in blocks:
        header = block.split("\n", 1)[0]
        if not header.startswith("[CELL"):
            continue

        cell_index = int(header.split("[CELL")[1].split("|")[0].strip())

        matches = pattern.findall(block)
        for fn in matches:
            func_map[fn] = cell_index

    return func_map


# =========================
# Example Usage
# =========================

if __name__ == "__main__":
    notebook_path = "recommend_product_myntra.ipynb"

    blocks = notebook_to_llm_blocks(notebook_path)

    # --- Example 1: Print full notebook ---
    print("\n".join(blocks))

    # --- Example 2: Only error cells ---
    # error_blocks = filter_has_error(blocks)
    # print("\n".join(error_blocks))

    # --- Example 3: Keyword focus ---
    # focused = filter_by_keyword(blocks, ["arima", "fit", "rmse"])
    # print("\n".join(focused))

    # --- Example 4: Cell range ---
    # focused = filter_by_cell_index(blocks, start=10, end=20)
    # print("\n".join(focused))

    # --- Example 5: Function → cell map ---
    # func_map = build_function_cell_map(blocks)
    # print(func_map)
