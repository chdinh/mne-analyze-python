from PySide6 import QtWidgets
import inspect
from rendercanvas.qt import RenderCanvas

print("RenderCanvas Source:")
try:
    print(inspect.getsource(RenderCanvas))
except Exception as e:
    print(f"Could not get source: {e}")
    print("MRO:", RenderCanvas.mro())
    print("Dir:", dir(RenderCanvas))
