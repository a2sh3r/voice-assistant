import ctypes
import os
import sys

if sys.platform == "win32":
    torch_lib = os.path.join(sys._MEIPASS, "torch", "lib")
    if os.path.exists(torch_lib):
        # Store in sys to prevent garbage collection — without this the
        # AddedDllDirectory cookie is immediately collected and the path removed.
        sys._torch_dll_dir = os.add_dll_directory(torch_lib)

        # Pre-load DLLs in dependency order so the Windows loader finds them
        # before torch/__init__.py tries to load them implicitly.
        for _dll in ["libiomp5md.dll", "uv.dll", "c10.dll", "torch_cpu.dll",
                     "torch_global_deps.dll", "torch.dll", "torch_python.dll"]:
            _dll_path = os.path.join(torch_lib, _dll)
            if os.path.exists(_dll_path):
                ctypes.CDLL(_dll_path)
