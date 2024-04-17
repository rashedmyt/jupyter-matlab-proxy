# Copyright 2023-2024 The MathWorks, Inc.
# Custom Exceptions used in MATLAB Kernel


class MATLABConnectionError(Exception):
    """
    A connection error occurred while connecting to MATLAB.

    Args:
        message (string): Error message to be displayed
    """

    def __init__(self, message=None):
        if message is None:
            message = 'Error connecting to MATLAB. Check the status of MATLAB by clicking the "Open MATLAB" button. Retry after ensuring MATLAB is running successfully'
        super().__init__(message)
