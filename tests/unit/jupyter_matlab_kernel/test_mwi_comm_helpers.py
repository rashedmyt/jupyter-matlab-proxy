# Copyright 2023-2024 The MathWorks, Inc.
# This file contains tests for jupyter_matlab_kernel.mwi_comm_helpers

import httpx
import pytest
from jupyter_matlab_kernel.mwi_comm_helpers import MatlabProxyCommunicationManager
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError
from mocks.mock_http_responses import (
    MockMatlabProxyStatusResponse,
    MockSimpleBadResponse,
    MockUnauthorisedRequestResponse,
)


@pytest.fixture
def matlab_proxy_fixture():
    url = "http://localhost"
    headers = {}
    matlab_proxy = MatlabProxyCommunicationManager(url, headers)
    return matlab_proxy


# Testing fetch_matlab_proxy_status
async def test_fetch_matlab_proxy_status_unauth_request(
    httpx_mock, matlab_proxy_fixture
):
    """
    This test checks that fetch_matlab_proxy_status throws an exception
    if the matlab-proxy HTTP request is unauthorised.
    """

    def mock_get(*args, **kwargs):
        return MockUnauthorisedRequestResponse()

    httpx_mock.add_callback(mock_get)
    with pytest.raises(httpx.HTTPError) as exceptionInfo:
        await matlab_proxy_fixture.fetch_matlab_proxy_status()
    assert MockUnauthorisedRequestResponse().exception_msg in str(exceptionInfo.value)


@pytest.mark.parametrize(
    "input_lic_type, expected_license_status",
    [
        ("mhlm_entitled", True),
        ("mhlm_unentitled", False),
        ("nlm", True),
        ("existing_license", True),
        ("default", False),
    ],
)
async def test_fetch_matlab_proxy_status(
    input_lic_type, expected_license_status, httpx_mock, matlab_proxy_fixture
):
    """
    This test checks that fetch_matlab_proxy_status returns the correct
    values for a valid request to matlab-proxy.
    """

    def mock_get(*args, **kwargs):
        return MockMatlabProxyStatusResponse(
            lic_type=input_lic_type, matlab_status="up", has_error=False
        )

    httpx_mock.add_callback(mock_get)

    (
        is_matlab_licensed,
        matlab_status,
        matlab_proxy_has_error,
    ) = await matlab_proxy_fixture.fetch_matlab_proxy_status()
    assert is_matlab_licensed == expected_license_status
    assert matlab_status == "up"
    assert matlab_proxy_has_error is False


async def test_interrupt_request_bad_request(httpx_mock, matlab_proxy_fixture):
    """
    This test checks that send_interrupt_request_to_matlab raises
    an exception if the response to the HTTP post is not valid.
    """

    mock_exception_message = "Mock exception thrown due to bad request status."

    def mock_post(*args, **kwargs):
        return MockSimpleBadResponse(mock_exception_message)

    httpx_mock.add_callback(mock_post)

    with pytest.raises(httpx.HTTPError) as exceptionInfo:
        await matlab_proxy_fixture.send_interrupt_request_to_matlab()
    assert mock_exception_message in str(exceptionInfo.value)


# Testing send_execution_request_to_matlab
async def test_execution_request_bad_request(httpx_mock, matlab_proxy_fixture):
    """
    This test checks that send_execution_request_to_matlab throws an exception
    if the response to the HTTP request is invalid.
    """
    mock_exception_message = "Mock exception thrown due to bad request status."

    def mock_post(*args, **kwargs):
        return MockSimpleBadResponse(mock_exception_message)

    httpx_mock.add_callback(mock_post)

    code = "placeholder for code"
    kernelid = ""
    with pytest.raises(httpx.HTTPError) as exceptionInfo:
        await matlab_proxy_fixture.send_execution_request_to_matlab(code, kernelid)
    assert mock_exception_message in str(exceptionInfo.value)


async def test_execution_request_invalid_feval_response(
    httpx_mock, matlab_proxy_fixture
):
    """
    This test checks that send_execution_request_to_matlab raises an exception
    if the response from the feval command is invalid.
    """
    mock_exception_message = "Mock exception thrown due to invalid feval response."

    class MockSimpleInvalidFevalResponse(httpx.Response):
        def __init__(self):
            super().__init__(status_code=httpx.codes.OK)

        def raise_for_status(self):
            raise httpx.HTTPError(mock_exception_message)

        @staticmethod
        def json():
            return {"messages": {}}

    def mock_post(*args, **kwargs):
        return MockSimpleInvalidFevalResponse()

    httpx_mock.add_callback(mock_post)

    code = "placeholder for code"
    kernelid = ""
    with pytest.raises(MATLABConnectionError) as exceptionInfo:
        await matlab_proxy_fixture.send_execution_request_to_matlab(code, kernelid)
    assert str(exceptionInfo.value) == str(MATLABConnectionError())


async def test_execution_interrupt(httpx_mock, matlab_proxy_fixture):
    """
    This test checks that send_execution_request_to_matlab raises an exception
    if the matlab command appears to have been interupted.
    """

    mock_exception_message = "Mock exception thrown due to bad request status."

    class MockResponse(httpx.Response):
        def __init__(self):
            super().__init__(status_code=httpx.codes.OK)

        def raise_for_status(self):
            raise httpx.HTTPError(mock_exception_message)

        @staticmethod
        def json():
            return {
                "messages": {
                    "FEvalResponse": [
                        {},
                        {
                            "isError": True,
                            "results": ["Mock results from feval"],
                            "messageFaults": [{"message": ""}],
                        },
                    ],
                }
            }

    def mock_post(*args, **kwargs):
        return MockResponse()

    httpx_mock.add_callback(mock_post)

    code = "placeholder for code"
    kernelid = ""
    with pytest.raises(Exception) as exceptionInfo:
        await matlab_proxy_fixture.send_execution_request_to_matlab(code, kernelid)
    assert "Operation may have interrupted by user" in str(exceptionInfo.value)


async def test_execution_success(httpx_mock, matlab_proxy_fixture):
    """
    This test checks that send_execution_request_to_matlab returns the correct information
    from a valid response from MATLAB.
    """

    class MockResponse(httpx.Response):
        def __init__(self):
            super().__init__(status_code=httpx.codes.OK)

        @staticmethod
        def json():
            return {
                "messages": {
                    "FEvalResponse": [
                        {},
                        {
                            "isError": False,
                            "results": ["Mock results from feval"],
                            "messageFaults": [{"message": ""}],
                        },
                    ],
                }
            }

    def mock_post(*args, **kwargs):
        return MockResponse()

    httpx_mock.add_callback(mock_post)

    code = "placeholder for code"
    kernelid = ""
    try:
        outputs = await matlab_proxy_fixture.send_execution_request_to_matlab(
            code, kernelid
        )
    except Exception:
        pytest.fail("Unexpected failured in execution request")

    assert "Mock results from feval" in outputs
