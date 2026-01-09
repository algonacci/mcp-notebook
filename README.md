# mcp-notebook

MCP server to give client the ability to analyze .ipynb file

# Usage

```json
{
  "mcpServers": {
    "notebook": {
      "command": "uv",
      "args": [
        "--directory",
        "%USERPROFILE%/Documents/GitHub/mcp-notebook",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```