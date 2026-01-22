import wgpu
print(f"WGPU Version: {wgpu.__version__}")
print(f"File: {wgpu.__file__}")

try:
    import wgpu.gui
    print(f"wgpu.gui found: {wgpu.gui.__file__}")
except ImportError as e:
    print(f"wgpu.gui NOT found: {e}")

try:
    from wgpu.gui.qt import WgpuCanvas
    print("wgpu.gui.qt.WgpuCanvas successfully imported")
except ImportError as e:
    print(f"wgpu.gui.qt import failed: {e}")

try:
    import rendercanvas
    print(f"rendercanvas found: {rendercanvas.__file__}")
except ImportError:
    print("rendercanvas NOT found")
