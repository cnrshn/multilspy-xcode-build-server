import asyncio
import argparse
import json
from typing import Any

from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

from multispy_xcode_build_server.server import XcodeBuildServer

def print_result(result: Any):
    print(json.dumps(result, indent=4))
async def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--workspace_path", type=str, required=True)
    parser.add_argument("--relative_file_path", type=str, required=True)
    parser.add_argument("--line", type=int, required=True)
    parser.add_argument("--column", type=int, required=True)

    args = parser.parse_args()

    WORKSPACE_PATH = args.workspace_path
    FILE_PATH = f"{WORKSPACE_PATH}/{args.relative_file_path}"
    LINE = args.line
    COLUMN = args.column


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

if __name__ == "__main__":
    asyncio.run(main())
