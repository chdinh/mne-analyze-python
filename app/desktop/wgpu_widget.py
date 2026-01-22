"""
WebGPU Widget Base Class for PySide6.

Provides an abstract base class for integrating WebGPU rendering with Qt widgets
using offscreen rendering and QPainter blitting.

Based on the NCCA/WebGPU pattern: https://github.com/NCCA/WebGPU
"""

from abc import ABCMeta, abstractmethod
from typing import List, Tuple

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QWidget


class QWidgetABCMeta(type(QWidget), ABCMeta):
    """Metaclass combining ABCMeta and QWidget's metaclass."""
    pass


class WebGPUWidget(QWidget, metaclass=QWidgetABCMeta):
    """
    Abstract base class for WebGPU widgets.

    Provides a template similar to QOpenGLWidget for creating WebGPU widgets.
    Subclasses must implement initializeWebGPU(), paintWebGPU(), and resizeWebGPU().

    The rendering approach:
    1. Subclass renders to an offscreen texture in paintWebGPU()
    2. Subclass reads back pixels into self.buffer (numpy RGBA array)
    3. This class blits self.buffer onto the widget using QPainter

    Attributes:
        initialized (bool): Whether initializeWebGPU() has been called.
        buffer (np.ndarray): RGBA pixel buffer to be blitted. Shape: (height, width, 4).
        text_buffer (list): Queued text items to render.
    """

    def __init__(self, parent=None):
        """Initialize the WebGPU widget."""
        super().__init__(parent)
        self.initialized = False
        self.buffer = None
        self.text_buffer: List[Tuple[int, int, str, int, str, QColor]] = []
        
        # Enable keyboard focus for key events
        self.setFocusPolicy(Qt.StrongFocus)

    @abstractmethod
    def initializeWebGPU(self) -> None:
        """
        Initialize the WebGPU context.
        
        Called once on first paint. Set up adapter, device, pipelines here.
        """
        pass

    @abstractmethod
    def paintWebGPU(self) -> None:
        """
        Render WebGPU content.
        
        Called every paint event. Must update self.buffer with the rendered pixels.
        The buffer should be a numpy array of shape (height, width, 4) with dtype uint8.
        """
        pass

    @abstractmethod
    def resizeWebGPU(self, width: int, height: int) -> None:
        """
        Handle resize of the WebGPU context.
        
        Called when the widget is resized. Recreate offscreen textures here.
        
        Args:
            width: New widget width in pixels.
            height: New widget height in pixels.
        """
        pass

    def paintEvent(self, event) -> None:
        """Handle Qt paint event."""
        if not self.initialized:
            self.initializeWebGPU()
            self.initialized = True
            
        self.paintWebGPU()
        
        painter = QPainter(self)
        
        # Blit the rendered buffer
        if self.buffer is not None:
            self._blit_buffer(painter)
            
        # Render text overlays
        for x, y, text, size, font, colour in self.text_buffer:
            painter.setPen(colour)
            painter.setFont(QFont(font, size))
            painter.drawText(x, y, text)
        self.text_buffer.clear()
        
        painter.end()

    def resizeEvent(self, event) -> None:
        """Handle Qt resize event."""
        size = event.size()
        if size.width() > 0 and size.height() > 0:
            self.resizeWebGPU(size.width(), size.height())
        super().resizeEvent(event)

    def render_text(
        self,
        x: int,
        y: int,
        text: str,
        size: int = 12,
        font: str = "Arial",
        colour: QColor = None,
    ) -> None:
        """
        Queue text to be rendered on the widget.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            text: Text string to render.
            size: Font size.
            font: Font family name.
            colour: Text color (default: white).
        """
        if colour is None:
            colour = QColor(Qt.white)
        self.text_buffer.append((x, y, text, size, font, colour))

    def _blit_buffer(self, painter: QPainter) -> None:
        """Blit the pixel buffer onto the widget."""
        if self.buffer is None:
            return
            
        height, width = self.buffer.shape[:2]
        
        # Disable smoothing for pixel-perfect blit
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform,
            False,
        )
        
        # Create QImage from buffer
        image = QImage(
            self.buffer.tobytes(),
            width,
            height,
            width * 4,
            QImage.Format.Format_RGBA8888,
        )
        
        # Draw scaled to widget size
        painter.drawImage(self.rect(), image)
