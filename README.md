# multispy-xcode-build-server

A build server implementation for Xcode projects using multispy.

## Installation

bash
pip install multispy-xcode-build-server

## Usage

```python
    config = MultilspyConfig.from_dict({"code_language": "swift"})
    logger = MultilspyLogger()

    lsp = XcodeBuildServer(config, logger, WORKSPACE_PATH)
    print(lsp)

    async with lsp.start_server():
        line = LINE
        column = COLUMN
        print("started")
        result = await lsp.request_definition(FILE_PATH, line, column)
        print_result(result)

        result = await lsp.request_hover(FILE_PATH, line, column)
        print_result(result)

        result = await lsp.request_document_symbols(FILE_PATH)
        print_result(result)

        result = await lsp.request_rename(FILE_PATH, line, column, "new_name")
        print_result(result)

        result = await lsp.request_workspace_symbols(" ")
        print_result(result)
```


## Development

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Run tests: `python -m pytest`

## Symbol Kinds
https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#symbolKind

## License

This project is licensed under the MIT License - see the LICENSE file for details.
