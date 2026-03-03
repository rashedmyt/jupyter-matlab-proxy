# Copyright 2024-2026 The MathWorks, Inc.

from jupyter_matlab_kernel.mpm_kernel import MATLABKernelUsingMPM


class KernelFactory:
    """
    KernelFactory class for determining and returning the appropriate MATLAB kernel class.

    This class provides a static method to decide between different MATLAB kernel
    implementations based on configuration settings.
    """

    @staticmethod
    def get_kernel_class() -> type[MATLABKernelUsingMPM]:
        """
        Determines and returns the appropriate MATLAB kernel class to use.

        Returns:
            MATLABKernelUsingMPM: The class of the MATLAB kernel to be used. This will
            be `type[MATLABKernelUsingMPM]` since that is the only supported Kernel configuration currently.
        """
        return MATLABKernelUsingMPM
