"""
Minimal wgpu.gui.qt test with direct draw_frame call.
"""
from PySide6 import QtWidgets, QtCore
import wgpu
from wgpu.gui.qt import WgpuCanvas
import sys

class TestCanvas(WgpuCanvas):
    def __init__(self):
        super().__init__()
        self.adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
        self.device = self.adapter.request_device_sync()
        self._frame_count = 0
        
    def draw_frame(self):
        self._frame_count += 1
        if self._frame_count <= 3:
            print(f"draw_frame called! Frame {self._frame_count}", flush=True)
            
        ctx = self.get_context("wgpu")
        ctx.configure(device=self.device, format=wgpu.TextureFormat.bgra8unorm)
        
        texture = ctx.get_current_texture()
        view = texture.create_view()
        
        # Simple render pass that clears to red
        encoder = self.device.create_command_encoder()
        render_pass = encoder.begin_render_pass(
            color_attachments=[{
                "view": view,
                "load_op": "clear",
                "store_op": "store",
                "clear_value": (1.0, 0.0, 0.0, 1.0),  # Red
            }]
        )
        render_pass.end()
        self.device.queue.submit([encoder.finish()])

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    canvas = TestCanvas()
    canvas.resize(800, 600)
    canvas.show()
    
    # Timer to call draw_frame directly
    timer = QtCore.QTimer()
    timer.timeout.connect(canvas.draw_frame)  # Direct call
    timer.start(16)  # ~60 FPS
    
    sys.exit(app.exec())
