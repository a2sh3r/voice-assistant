import os
import sys

if sys.platform == "win32":
    torch_lib = os.path.join(sys._MEIPASS, "torch", "lib")
    if os.path.exists(torch_lib):
        os.add_dll_directory(torch_lib)
