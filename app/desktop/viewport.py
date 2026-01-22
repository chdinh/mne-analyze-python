"""
WebGPU Viewport for the Brain Viewer.

Implements the concrete WebGPU widget for brain rendering using offscreen
texture rendering and pixel readback.
"""

import numpy as np
import wgpu
from PySide6 import QtCore

from app.desktop.wgpu_widget import WebGPUWidget


class WgpuViewport(WebGPUWidget):
    """
    A PySide6 widget that renders the brain using WebGPU.
    
    Uses offscreen rendering: renders to a texture, reads back pixels,
    and blits to the widget using QPainter.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = None
        self.camera = None
        
        # WebGPU resources
        self.adapter = None
        self.device = None
        self.render_texture = None
        self.depth_texture = None
        self.render_width = 800
        self.render_height = 600

    def set_renderer(self, renderer):
        """Set the brain renderer."""
        self.renderer = renderer

    def set_camera(self, camera):
        """Set the camera for navigation."""
        self.camera = camera

    def initializeWebGPU(self) -> None:
        """Initialize WebGPU adapter, device, and offscreen textures."""
        self.adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
        self.device = self.adapter.request_device_sync()
        
        # Create initial offscreen textures
        self._create_offscreen_textures(self.render_width, self.render_height)

    def resizeWebGPU(self, width: int, height: int) -> None:
        """Recreate offscreen textures on resize."""
        if width > 0 and height > 0:
            self.render_width = width
            self.render_height = height
            if self.device:
                self._create_offscreen_textures(width, height)

    def _create_offscreen_textures(self, width: int, height: int) -> None:
        """Create offscreen render and depth textures."""
        # Color texture for rendering
        self.render_texture = self.device.create_texture(
            size=(width, height, 1),
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
        )
        
        # Depth texture
        self.depth_texture = self.device.create_texture(
            size=(width, height, 1),
            format=wgpu.TextureFormat.depth24plus,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        )

    def paintWebGPU(self) -> None:
        """Render the brain to offscreen texture and read back pixels."""
        if not self.device or not self.renderer or not self.camera:
            # Create a blank buffer if not ready
            self.buffer = np.zeros((self.render_height, self.render_width, 4), dtype=np.uint8)
            self.buffer[:, :, 3] = 255  # Opaque black
            return
            
        # Ensure textures match current size
        if self.render_texture.size[0] != self.render_width or self.render_texture.size[1] != self.render_height:
            self._create_offscreen_textures(self.render_width, self.render_height)
        
        # Get texture view
        render_view = self.render_texture.create_view()
        
        # Calculate aspect ratio
        aspect = self.render_width / max(self.render_height, 1)
        
        # Get camera matrix
        view_matrix = self.camera.get_view_matrix()
        
        # Ensure renderer uses our device
        if self.renderer.device != self.device:
            # This shouldn't happen if we set up correctly
            pass
        
        # Render the brain
        self.renderer.draw(
            target_texture_view=render_view,
            aspect_ratio=aspect,
            view_matrix=view_matrix,
            camera_pos=self.camera.position,
            depth_texture=self.depth_texture,
        )
        
        # Read back pixels from render texture
        self.buffer = self._read_texture_pixels()

    def _read_texture_pixels(self) -> np.ndarray:
        """Read pixels from the render texture into a numpy array."""
        width = self.render_width
        height = self.render_height
        
        # Bytes per row must be aligned to 256 bytes
        bytes_per_row = width * 4
        aligned_bytes_per_row = (bytes_per_row + 255) // 256 * 256
        
        # Create buffer for readback
        buffer_size = aligned_bytes_per_row * height
        readback_buffer = self.device.create_buffer(
            size=buffer_size,
            usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ,
        )
        
        # Copy texture to buffer
        encoder = self.device.create_command_encoder()
        encoder.copy_texture_to_buffer(
            {
                "texture": self.render_texture,
                "origin": (0, 0, 0),
            },
            {
                "buffer": readback_buffer,
                "offset": 0,
                "bytes_per_row": aligned_bytes_per_row,
                "rows_per_image": height,
            },
            (width, height, 1),
        )
        self.device.queue.submit([encoder.finish()])
        
        # Map and read buffer
        readback_buffer.map_sync(mode=wgpu.MapMode.READ)
        data = readback_buffer.read_mapped()
        readback_buffer.unmap()
        
        # Convert to numpy, handling row alignment
        pixels = np.frombuffer(data, dtype=np.uint8)
        pixels = pixels.reshape((height, aligned_bytes_per_row // 4, 4))
        pixels = pixels[:, :width, :]  # Remove padding
        
        return pixels.copy()

    # ─────────────────────────────────────────────────────────────────────────
    # Mouse Event Handling
    # ─────────────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if self.camera:
            self.camera.handle_event({
                "event_type": "pointer_down",
                "x": event.position().x(),
                "y": event.position().y(),
                "button": 1 if event.button() == QtCore.Qt.MouseButton.LeftButton else 2,
            })
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.camera:
            self.camera.handle_event({
                "event_type": "pointer_up",
                "x": event.position().x(),
                "y": event.position().y(),
                "button": 0,
            })
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.camera:
            self.camera.handle_event({
                "event_type": "pointer_move",
                "x": event.position().x(),
                "y": event.position().y(),
                "button": 0,
            })
            self.update()  # Request repaint on mouse move for responsive interaction
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if self.camera:
            self.camera.handle_event({
                "event_type": "wheel",
                "dy": -event.angleDelta().y(),
                "x": event.position().x(),
                "y": event.position().y(),
            })
            self.update()  # Request repaint on wheel for responsive zoom
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Forward key events to parent for handling."""
        # Let parent handle key events
        event.ignore()
