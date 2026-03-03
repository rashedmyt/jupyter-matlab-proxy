# Copyright 2020-2026 The MathWorks, Inc.

import os
import secrets
from pathlib import Path

import matlab_proxy_manager
import matlab_proxy_manager.utils.environment_variables as mpm_env
from matlab_proxy.util.mwi import logger as mwi_logger
from matlab_proxy_manager.utils import constants

_MPM_AUTH_TOKEN: str = secrets.token_hex(32)
_JUPYTER_SERVER_PID: str = str(os.getpid())


def _get_env(port, base_url):
    """Returns a dict containing environment settings to launch the MATLAB Desktop

    Args:
        port (int): Port number on which the MATLAB Desktop will be started. Ex: 8888
        base_url (str): Controls the prefix in the url on which MATLAB Desktop will be available.
                        Ex: localhost:8888/base_url/index.html

    Returns:
        [Dict]: Containing environment settings to launch the MATLAB Desktop.
    """

    return {
        mpm_env.get_env_name_mwi_mpm_port(): str(port),
        mpm_env.get_env_name_mwi_mpm_auth_token(): _MPM_AUTH_TOKEN,
        mpm_env.get_env_name_mwi_mpm_parent_pid(): _JUPYTER_SERVER_PID,
        mpm_env.get_env_name_base_url_prefix(): f"{base_url}",
    }


def setup_matlab():
    """This method is run by jupyter-server-proxy package with instruction to launch the MATLAB Desktop

    Returns:
        [Dict]: Containing information to launch the MATLAB Desktop.
    """

    logger = mwi_logger.get(init=True)
    logger.info("Initializing Jupyter MATLAB Proxy")

    jsp_config = _get_jsp_config(logger=logger)

    return jsp_config


def _get_jsp_config(logger):
    icon_path = str(Path(__file__).parent / "icon_open_matlab.svg")
    logger.debug("Icon_path: %s", icon_path)
    jsp_config = {
        # Starts proxy manager process which in turn starts a shared matlab proxy instance
        # if not already started. This gets invoked on clicking `Open MATLAB` button and would
        # always take the user to the default (shared) matlab-proxy instance.
        "command": [matlab_proxy_manager.get_executable_name()],
        "timeout": 100,  # timeout in seconds
        "environment": _get_env,
        "absolute_url": True,
        "launcher_entry": {"title": "Open MATLAB", "icon_path": icon_path},
    }
    logger.debug("Launch Command: %s", jsp_config.get("command"))

    # Add jupyter server pid and mpm_auth_token to the request headers for resource
    # filtering and Jupyter to proxy manager authentication
    jsp_config["request_headers_override"] = {
        constants.HEADER_MWI_MPM_CONTEXT: _JUPYTER_SERVER_PID,
        constants.HEADER_MWI_MPM_AUTH_TOKEN: _MPM_AUTH_TOKEN,
    }

    return jsp_config
