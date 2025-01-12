import asyncio
import json
import logging
import os
from pathlib import PurePath
import pathlib
from typing import Dict, List, Optional, TypedDict, Union, Any
from contextlib import asynccontextmanager
from typing import AsyncIterator
from typing_extensions import NotRequired

import uuid
from multilspy.language_server import LanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from multilspy.multilspy_settings import MultilspySettings
from multilspy.lsp_protocol_handler.server import ProcessLaunchInfo
from multilspy.lsp_protocol_handler.lsp_types import InitializeParams
from multilspy import multilspy_types
from multilspy.multilspy_exceptions import MultilspyException

class TextEdit(TypedDict):
    """Represents a text edit operation to be performed on a document."""
    range: multilspy_types.Range
    newText: str

class LocationWithoutRange(TypedDict):
    """A location without a range."""
    uri: str

class WorkspaceSymbol(TypedDict):
    """A special workspace symbol that supports locations without a range."""
    name: str
    kind: int
    location: Union[multilspy_types.Location, LocationWithoutRange]
    tags: NotRequired[List[int]]
    containerName: NotRequired[str]
    data: NotRequired[Any]

class XcodeBuildServer(LanguageServer):
    """
    Main class for the Xcode build server implementation
    """
    
    def __init__(self, config: MultilspyConfig, logger: MultilspyLogger, repository_root_path: str):
        """
        Creates a new EclipseJDTLS instance initializing the language server settings appropriately.
        This class is not meant to be instantiated directly. Use LanguageServer.create() instead.
        """

        proc_env = {}
        proc_cwd = repository_root_path
        cmd = " ".join(
            [
                "sourcekit-lsp"
            ]
        )

        self.service_ready_event = asyncio.Event()

        super().__init__(config, logger, repository_root_path, ProcessLaunchInfo(cmd, proc_env, proc_cwd), "swift")


    def _get_initialize_params(self, repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize parameters for the XcodeBuildServer server.
        """

        with open(str(PurePath(os.path.dirname(__file__), "initialize_params.json")), "r") as f:
            d: InitializeParams = json.load(f)

        if not os.path.isabs(repository_absolute_path):
            repository_absolute_path = os.path.abspath(repository_absolute_path)

        assert d["processId"] == "os.getpid()"
        d["processId"] = os.getpid()

        assert d["rootPath"] == "repository_absolute_path"
        d["rootPath"] = repository_absolute_path

        assert d["rootUri"] == "pathlib.Path(repository_absolute_path).as_uri()"
        d["rootUri"] = pathlib.Path(repository_absolute_path).as_uri()

        assert (
            d["workspaceFolders"]
            == '[\n            {\n                "uri": pathlib.Path(repository_absolute_path).as_uri(),\n                "name": os.path.basename(repository_absolute_path),\n            }\n        ]'
        )
        d["workspaceFolders"] = [
            {
                "uri": pathlib.Path(repository_absolute_path).as_uri(),
                "name": os.path.basename(repository_absolute_path),
            }
        ]



        return d

    @asynccontextmanager
    async def start_server(self) -> AsyncIterator["XcodeBuildServer"]:
        """
        Starts the XcodeBuildServer, waits for the server to be ready and yields the LanguageServer instance.

        Usage:
        ```
        async with lsp.start_server():
            # LanguageServer has been initialized and ready to serve requests
            await lsp.request_definition(...)
            await lsp.request_references(...)
            # Shutdown the LanguageServer on exit from scope
        # LanguageServer has been shutdown
        ```
        """

        async def register_capability_handler(params):
            assert "registrations" in params
            for registration in params["registrations"]:
                if registration["method"] == "textDocument/completion":
                    assert registration["registerOptions"]["resolveProvider"] == True
                    assert registration["registerOptions"]["triggerCharacters"] == [
                        ".",
                        "@",
                        "#",
                        "*",
                        " ",
                    ]
                    self.completions_available.set()
            return

        async def lang_status_handler(params):
            # TODO: Should we wait for
            # server -> client: {'jsonrpc': '2.0', 'method': 'language/status', 'params': {'type': 'ProjectStatus', 'message': 'OK'}}
            # Before proceeding?
            if params["type"] == "ServiceReady" and params["message"] == "ServiceReady":
                self.service_ready_event.set()

        async def execute_client_command_handler(params):
            #assert params["command"] == "_java.reloadBundles.command"
            #assert params["arguments"] == []
            return []

        async def window_log_message(msg):
            self.logger.log(f"LSP: window/logMessage: {msg}", logging.INFO)

        async def do_nothing(params):
            return

        self.server.on_request("client/registerCapability", register_capability_handler)
        self.server.on_notification("language/status", lang_status_handler)
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_request("workspace/executeClientCommand", execute_client_command_handler)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)
        self.server.on_notification("language/actionableNotification", do_nothing)

        async with super().start_server():
            self.logger.log("Starting XcodeBuildServer server process", logging.INFO)
            await self.server.start()
            initialize_params = self._get_initialize_params(self.repository_root_path)

            self.logger.log(
                "Sending initialize request from LSP client to LSP server and awaiting response",
                logging.INFO,
            )
            init_response = await self.server.send.initialize(initialize_params)
            assert init_response["capabilities"]["textDocumentSync"]["change"] == 2

            self.server.notify.initialized({})


            # TODO: Add comments about why we wait here, and how this can be optimized
            # await self.service_ready_event.wait()

            yield self

            await self.server.shutdown()
            await self.server.stop()

    async def request_rename(
        self, relative_file_path: str, line: int, column: int, new_name: str
    ) -> Dict[str, List[TextEdit]]:
        """
        Raise a [textDocument/rename](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_rename) request to the Language Server
        to rename the symbol at the given line and column in the given file to the new name. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbol to rename
        :param line: The line number of the symbol
        :param column: The column number of the symbol
        :param new_name: The new name for the symbol

        :return Dict[str, List[TextEdit]]: A dictionary mapping file URIs to lists of text edits to be applied
        """
        if not self.server_started:
            self.logger.log(
                "request_rename called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        with self.open_file(relative_file_path):
            # sending request to the language server and waiting for response
            response = await self.server.send.rename(
                {
                    "textDocument": {
                        "uri": pathlib.Path(os.path.join(self.repository_root_path, relative_file_path)).as_uri()
                    },
                    "position": {"line": line, "character": column},
                    "newName": new_name
                }
            )

        ret: Dict[str, List[TextEdit]] = {}
        assert isinstance(response, dict)
        assert "changes" in response

        for uri, changes in response["changes"].items():
            assert isinstance(changes, list)
            edits: List[TextEdit] = []
            for change in changes:
                assert isinstance(change, dict)
                assert "range" in change
                assert "newText" in change
                edits.append(TextEdit(**change))
            ret[uri] = edits

        return ret

    async def request_workspace_symbols(self, query: str) -> List[WorkspaceSymbol]:
        """
        Raise a [workspace/symbol](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol) request to the Language Server
        to search for symbols matching the query across all files in the workspace. Wait for the response and return the result.

        :param query: The query string to match against symbol names

        :return List[WorkspaceSymbol]: A list of workspace symbols matching the query
        """
        if not self.server_started:
            self.logger.log(
                "request_workspace_symbols called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        response = await self.server.send.workspace_symbol({"query": query})
        if response is None:
            return []

        ret: List[WorkspaceSymbol] = []
        assert isinstance(response, list)

        for item in response:
            assert isinstance(item, dict)
            # Create base symbol with required fields
            symbol: WorkspaceSymbol = {
                "name": item["name"],
                "kind": item["kind"],
                "location": (
                    item["location"] if isinstance(item["location"], dict) and "range" in item["location"]
                    else {"uri": item["location"]["uri"]}
                )
            }
            
            # Add optional fields if present
            for field in ["containerName", "tags", "data"]:
                if field in item:
                    symbol[field] = item[field]
            
            ret.append(symbol)

        return ret