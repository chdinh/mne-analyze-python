"""
MNE Analyze Python - PySide6 Desktop Application

Entry point for the PySide6 desktop app with embedded WebGPU brain viewer.
Uses QRenderWidget from rendercanvas.qt for native Qt-WebGPU integration.
"""

import sys
from PySide6.QtWidgets import QApplication

from app.desktop.main_window import MainWindow


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("MNE Analyze Python")
    
    # Apply dark theme
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1a1a2e;
            color: #e0e0e0;
        }
        QDockWidget {
            color: #e0e0e0;
        }
        QDockWidget::title {
            background-color: #2d2d44;
            padding: 8px;
        }
        QPushButton {
            padding: 8px 16px;
            background-color: #4a90d9;
            color: white;
            border: none;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #5aa0e9;
        }
        QPushButton:pressed {
            background-color: #3a80c9;
        }
        QPushButton:checked {
            background-color: #2e7d32;
        }
        QComboBox {
            padding: 6px 12px;
            background-color: #2d2d44;
            color: #e0e0e0;
            border: 1px solid #4a4a6a;
            border-radius: 4px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QCheckBox {
            color: #e0e0e0;
            spacing: 8px;
        }
        QLabel {
            color: #e0e0e0;
        }
        QSlider::groove:horizontal {
            height: 4px;
            background: #4a4a6a;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            width: 16px;
            height: 16px;
            margin: -6px 0;
            background: #4a90d9;
            border-radius: 8px;
        }
    """)
    
    window = MainWindow()
    window.show()
    
    print("MNE Analyze Python started.")
    print("Controls: Left Click to Orbit, Right Click to Pan, Scroll to Zoom.")
    print("Key 't': Toggle Source Animation / Atlas Colors.")
    print("Key 'p': Toggle Butterfly Plot.")
    print("Key 'Space': Play/Pause.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
