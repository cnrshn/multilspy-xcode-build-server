# multispy-xcode-build-server

Swift language support for [microsoft/multilspy](https://github.com/microsoft/multilspy) using sourcekit-lsp.

## Overview

This repository extends multilspy's language support to include Swift, enabling static analysis of Swift codebases through the Language Server Protocol (LSP). It integrates with sourcekit-lsp to provide the same powerful static analysis capabilities that multilspy offers for other languages.

## Prerequisites

- Python 3.8 or higher
- Xcode and sourcekit-lsp installed
- `sourcekit-lsp` in your PATH

## Installation

```bash
pip install multispy-xcode-build-server
```

## Usage

```python
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from multispy_xcode_build_server import XcodeBuildServer

# Initialize the server
config = MultilspyConfig.from_dict({"code_language": "swift"})
logger = MultilspyLogger()

# Create server instance with your workspace path
lsp = XcodeBuildServer(config, logger, WORKSPACE_PATH)

# Use the server
async with lsp.start_server():
    # Find symbol definition
    definition = await lsp.request_definition(FILE_PATH, line, column)
    
    # Get hover information
    hover = await lsp.request_hover(FILE_PATH, line, column)
    
    # Get document symbols
    symbols = await lsp.request_document_symbols(FILE_PATH)
    
    # Rename symbol
    edits = await lsp.request_rename(FILE_PATH, line, column, "new_name")
    
    # Search workspace symbols
    workspace_symbols = await lsp.request_workspace_symbols("query")
```

## Features

This extension supports all standard LSP features provided by sourcekit-lsp:

- Symbol Definition Lookup
- Symbol References Search
- Code Completion
- Hover Information
- Document Symbols
- Workspace Symbol Search
- Symbol Renaming

## Integration with multilspy

This package is designed to work seamlessly with [microsoft/multilspy](https://github.com/microsoft/multilspy), a library developed as part of research for the NeurIPS 2023 paper "Monitor-Guided Decoding of Code LMs with Static Analysis of Repository Context". multilspy provides:

- Language-agnostic static analysis through LSP
- Automated server management
- Simplified API for static analysis queries
- Support for multiple programming languages

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   python -m pytest
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
