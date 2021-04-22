# Copyright 2021 The MathWorks, Inc.

from jupyter_matlab_proxy.devel import xvfb
import pytest, asyncio, aiohttp, os, json, psutil, socket, subprocess, time, requests
from unittest.mock import patch
from aiohttp import web
from jupyter_matlab_proxy import app, settings
from jupyter_matlab_proxy.util.exceptions import MatlabInstallError
from subprocess import Popen, PIPE
from jupyter_matlab_proxy.app_state import AppState
from distutils.dir_util import copy_tree
from pathlib import Path


def test_create_app():
    """Test if aiohttp server is being created successfully.

    Checks if the aiohttp server is created successfully, routes, startup and cleanup
    tasks are added.
    """
    test_server = app.create_app()

    # Verify router is configured with some routes
    assert test_server.router._resources is not None

    # Verify app server has startup and cleanup tasks
    # By default there is 1 start up and clean up task
    assert len(test_server._on_startup) > 1
    assert len(test_server.on_cleanup) > 1


def get_email():
    """A helper method which returns a placeholder email

    Returns:
        String: A placeholder email as a string.
    """
    return "abc@mathworks.com"


def get_connection_string():
    """A helper method which returns a placeholder nlm connection string

    Returns:
        String : A placeholder nlm connection string
    """
    return "nlm@localhost.com"


@pytest.fixture(
    name="licensing_data",
    params=[
        {"input": None, "expected": None},
        {
            "input": {"type": "mhlm", "email_addr": get_email()},
            "expected": {
                "type": "MHLM",
                "emailAddress": get_email(),
                "entitlements": [],
                "entitlementId": None,
            },
        },
        {
            "input": {"type": "nlm", "conn_str": get_connection_string()},
            "expected": {"type": "NLM", "connectionString": get_connection_string()},
        },
    ],
    ids=[
        "No Licensing info  supplied",
        "Licensing type is MHLM",
        "Licensing type is NLM",
    ],
)
def licensing_info_fixture(request):
    """A pytest fixture which returns licensing_data

    A parameterized pytest fixture which returns a licensing_data dict.
    licensing_data of three types:
        None : No licensing
        MHLM : Matlab Hosted License Manager
        NLM : Network License Manager.


    Args:
        request : A built-in pytest fixture

    Returns:
        Array : Containing expected and actual licensing data.
    """
    return request.param


def test_marshal_licensing_info(licensing_data):
    """Test app.marshal_licensing_info method works correctly

    This test checks if app.marshal_licensing_info returns correct licensing data.
    Test checks for 3 cases:
        1) No Licensing Provided
        2) MHLM type Licensing
        3) NLM type licensing

    Args:
        licensing_data (Array): An array containing actual and expected licensing data to assert.
    """

    actual_licensing_info = licensing_data["input"]
    expected_licensing_info = licensing_data["expected"]

    assert app.marshal_licensing_info(actual_licensing_info) == expected_licensing_info


@pytest.mark.parametrize(
    "actual_error, expected_error",
    [
        (None, None),
        (
            MatlabInstallError("'matlab' executable not found in PATH"),
            {
                "message": "'matlab' executable not found in PATH",
                "logs": None,
                "type": MatlabInstallError.__name__,
            },
        ),
    ],
    ids=["No error", "Raise Matlab Install Error"],
)
def test_marshal_error(actual_error, expected_error):
    """Test if marshal_error returns an expected Dict when an error is raised

    Upon raising MatlabInstallError, checks if the the relevant information is returned as a
    Dict.

    Args:
        actual_error (Exception): An instance of Exception class
        expected_error (Dict): A python Dict containing information on the type of Exception
    """
    assert app.marshal_error(actual_error) == expected_error


class MockServerPort:
    """A class used for Mocking reserve_port methods

    This class is used for mocking jupnter_matlab_proxy.app_state.AppState.reserve_matlab_port()
    In dev mode, reserve_matlab_port() will always reserve port 31515, which can cause issues when executing
    multiple tests together.

    Attributes:
        matlab_port : A integer indicating the port that is reserved for matlab.
    """

    def __init__(self):
        """Initializes MockServerPort class with matlab_port as None"""
        self.matlab_port = None

    def mock_reserve_port(self):
        """Reserves a random port made available by the OS and uses it as the matlab port.

        This method mocks the AppState.reserve_matlab_port() method. Acquires a random port made available
        by the OS and uses it as the matlab port. This will modify the matlab_port attribute defined in AppState.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        matlab_port = s.getsockname()[1]
        self.matlab_port = matlab_port
        s.close()


class FakeServer:
    """Context Manager class which returns a web server wrapped by aiohttp_client
    for sending HTTP requests during testing.

    executes the remove_zombie_matlab_process() method before starting the server
    and after shutting it down so as to clear out any
    """

    def __init__(self, loop, aiohttp_client):
        self.loop = loop
        self.aiohttp_client = aiohttp_client
        self.pretest_dev_processes = None
        self.posttest_dev_processes = None
        self.zombie_dev_processes = None

    def __enter__(self):

        self.pretest_dev_processes = set(self.gather_running_dev_processes())

        self.patcher = patch(
            "jupyter_matlab_proxy.app_state.AppState.reserve_matlab_port",
            new=MockServerPort.mock_reserve_port,
        )

        self.patcher.start()

        self.server = app.create_app()
        self.runner = web.AppRunner(self.server)

        self.loop.run_until_complete(self.runner.setup())

        self.site = web.TCPSite(
            self.runner,
            host=self.server["settings"]["host_interface"],
            port=self.server["settings"]["app_port"],
        )

        self.loop.run_until_complete(self.site.start())
        return self.loop.run_until_complete(self.aiohttp_client(self.server))

    def __exit__(self, exc_type, exc_value, exc_traceback):

        self.loop.run_until_complete(self.runner.shutdown())
        self.loop.run_until_complete(self.runner.cleanup())

        self.patcher.stop()

        self.posttest_dev_processes = set(self.gather_running_dev_processes())
        self.zombie_dev_processes = (
            self.posttest_dev_processes - self.pretest_dev_processes
        )

        for process in self.zombie_dev_processes:
            process.terminate()

        gone, alive = psutil.wait_procs(self.zombie_dev_processes)

        for process in alive:
            process.kill()

    def gather_running_dev_processes(self):
        running_dev_processes = []
        for process in psutil.process_iter(["pid", "name"]):
            cmd = process.cmdline()
            if len(cmd) > 3 and "devel.py" in cmd[2]:
                running_dev_processes.append(process)

        return running_dev_processes


@pytest.fixture(name="test_server")
def test_server_fixture(
    loop,
    aiohttp_client,
    mock_settings_get_custom_ready_delay,
):
    """A pytest fixture which yields a test server to be used by tests.

    Args:
        loop (Event loop): The built-in event loop provided by pytest.
        aiohttp_client (aiohttp_client): Built-in pytest fixture used as a wrapper to the aiohttp web server.
        matlab_port_setup (Integer): A pytest fixture which allocates a port and NLM connection string for matlab.

    Yields:
        aiohttp_client : A aiohttp_client server used by tests.
    """

    with FakeServer(loop, aiohttp_client) as test_server:
        yield test_server


async def test_get_status_route(test_server):
    """Test to check endpoint : "/get_status"

    Args:
        test_server (aiohttp_client): A aiohttp_client server for sending GET request.
    """

    resp = await test_server.get("/get_status")
    assert resp.status == 200


@pytest.fixture(name="proxy_payload")
def proxy_payload_fixture():
    """Pytest fixture which returns a Dict representing the payload.

    Returns:
        Dict: A Dict representing the payload for HTTP request.
    """
    payload = {"messages": {"ClientType": [{"properties": {"TYPE": "jsd"}}]}}

    return payload


async def test_matlab_proxy_404(proxy_payload, test_server):
    """Test to check if test_server is able to proxy HTTP request to fake matlab server
    for a non-existing file. Should return 404 status code in response

    Args:
        proxy_payload (Dict): Pytest fixture which returns a Dict.
        test_server (aiohttp_client): Test server to send HTTP requests.
    """

    headers = {"content-type": "application/json"}

    # Request a non-existing html file. Request gets proxied to app.matlab_view() which should raise HTTPNotFound() exception ie. return HTTP status code 404
    resp = await test_server.post(
        "./1234.html", data=json.dumps(proxy_payload), headers=headers
    )
    assert resp.status == 404


async def test_matlab_proxy_web_socket(test_server):
    """Test to check if test_server proxies web socket request to fake matlab server

    Args:
        test_server (aiohttp_client): Test Server to send HTTP Requests.
    """

    headers = {
        "connection": "Upgrade",
        "upgrade": "websocket",
    }

    resp = await test_server.ws_connect("/http_ws_request.html", headers=headers)
    text = await resp.receive()
    assert text.type == aiohttp.WSMsgType.CLOSED


async def test_set_licensing_info_put(test_server):
    """Test to check endpoint : "/set_licensing_info"

    Test which sends HTTP PUT request with NLM licensing information.
    Args:
        test_server (aiohttp_client): A aiohttp_client server to send HTTP GET request.
    """

    data = {
        "type": "NLM",
        "status": "starting",
        "version": "R2020b",
        "connectionString": "abc@nlm",
    }
    resp = await test_server.put("/set_licensing_info", data=json.dumps(data))
    assert resp.status == 200


async def test_set_licensing_info_delete(test_server):
    """Test to check endpoint : "/set_licensing_info"

    Test which sends HTTP DELETE request to remove licensing. Checks if licensing is set to None
    After request is sent.
    Args:
        test_server (aiohttp_client):  A aiohttp_client server to send HTTP GET request.
    """

    resp = await test_server.delete("/set_licensing_info")
    resp_json = json.loads(await resp.text())
    assert resp.status == 200 and resp_json["licensing"] is None
