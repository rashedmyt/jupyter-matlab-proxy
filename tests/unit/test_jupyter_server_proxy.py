# Copyright 2020-2026 The MathWorks, Inc.

import inspect
import os
from pathlib import Path

import jupyter_matlab_proxy
import matlab_proxy_manager
from matlab_proxy_manager.utils import constants
from matlab_proxy_manager.utils import environment_variables as mpm_env


def test_get_env_with_proxy_manager(monkeypatch):
    """Tests if _get_env() method returns the expected environment settings as a dict."""
    # Setup
    monkeypatch.setattr("jupyter_matlab_proxy._MPM_AUTH_TOKEN", "secret")
    monkeypatch.setattr("jupyter_matlab_proxy._JUPYTER_SERVER_PID", "123")
    mpm_port = 10000
    r = jupyter_matlab_proxy._get_env(mpm_port, None)
    assert r.get(mpm_env.get_env_name_mwi_mpm_port()) == str(mpm_port)
    assert r.get(mpm_env.get_env_name_mwi_mpm_auth_token()) == "secret"
    assert r.get(mpm_env.get_env_name_mwi_mpm_parent_pid()) == "123"


def test_setup_matlab_with_proxy_manager(monkeypatch):
    """Tests for a valid Server Process Configuration Dictionary

    This test checks if the jupyter proxy returns the expected Server Process Configuration
    Dictionary for the Matlab process.
    """

    # Setup
    monkeypatch.setattr("jupyter_matlab_proxy._MPM_AUTH_TOKEN", "secret")
    monkeypatch.setattr("jupyter_matlab_proxy._JUPYTER_SERVER_PID", "123")
    package_path = Path(inspect.getfile(jupyter_matlab_proxy)).parent
    icon_path = str(package_path / "icon_open_matlab.svg")

    expected_matlab_setup = {
        "command": [matlab_proxy_manager.get_executable_name()],
        "timeout": 100,
        "environment": jupyter_matlab_proxy._get_env,
        "absolute_url": True,
        "launcher_entry": {
            "title": "Open MATLAB",
            "icon_path": icon_path,
        },
        "request_headers_override": {
            constants.HEADER_MWI_MPM_CONTEXT: "123",
            constants.HEADER_MWI_MPM_AUTH_TOKEN: "secret",
        },
    }

    actual_matlab_setup = jupyter_matlab_proxy.setup_matlab()

    assert expected_matlab_setup == actual_matlab_setup
    assert os.path.isfile(actual_matlab_setup["launcher_entry"]["icon_path"])
