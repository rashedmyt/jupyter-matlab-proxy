# Copyright 2024-2026 The MathWorks, Inc.

from jupyter_matlab_kernel.kernel_factory import KernelFactory
from jupyter_matlab_kernel.mpm_kernel import MATLABKernelUsingMPM


def test_correct_kernel_type_is_returned():
    """
    Test that the correct kernel type is returned

    This test verifies that the `get_kernel_class` method of the `KernelFactory` class
    returns the expected kernel class, which is `MATLABKernelUsingMPM`."""
    kernel_class = KernelFactory.get_kernel_class()
    assert kernel_class is MATLABKernelUsingMPM
