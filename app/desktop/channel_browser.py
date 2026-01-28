import mne
from PySide6 import QtWidgets, QtCore
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class ChannelBrowser(QtWidgets.QWidget):
    """
    Widget that embeds MNE's raw data browser.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.raw = None
        self.canvas = None
        self.figure = None
        self.toolbar = None
        
        # Placeholder Label
        self.placeholder = QtWidgets.QLabel("Select a .fif file to view channels")
        self.placeholder.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.placeholder)

    def load_raw(self, file_path):
        """Load a raw file and display it."""
        try:
            # Clear previous
            if self.canvas:
                self.layout.removeWidget(self.canvas)
                self.canvas.deleteLater()
                self.canvas = None
                self.figure = None
                plt.close('all') # Cleanup matplotlib figures

            if self.toolbar:
                self.layout.removeWidget(self.toolbar)
                self.toolbar.deleteLater()
                self.toolbar = None

            if self.placeholder.isVisible():
                self.placeholder.setVisible(False)

            print(f"Loading raw file: {file_path}")
            self.raw = mne.io.read_raw_fif(file_path, preload=False)

            # Clean up previous browser/canvas
            # If we had a matplotlib canvas
            if self.canvas:
                self.layout.removeWidget(self.canvas)
                self.canvas.deleteLater()
                self.canvas = None
            
            # If we had a toolbar
            if self.toolbar:
                self.layout.removeWidget(self.toolbar)
                self.toolbar.deleteLater()
                self.toolbar = None
            
            # Try to use mne-qt-browser
            try:
                mne.viz.set_browser_backend("qt")
            except ImportError:
                 print("mne-qt-browser not found, falling back to matplotlib")
                 mne.viz.set_browser_backend("matplotlib")

            # Plot - returns the browser widget (if qt) or Figure (if mpl)
            # We don't pass 'fig' here as per the error fix.
            self.browser_view = self.raw.plot(show=False, block=False)
            
            # Embed
            if isinstance(self.browser_view, QtWidgets.QWidget):
                # If it's a QMainWindow (which MNE Qt Browser is), we need to handle it carefully
                # so it can be embedded in a layout.
                self.browser_view.setWindowFlags(QtCore.Qt.Widget)
                self.layout.addWidget(self.browser_view)
                self.canvas = self.browser_view # Keep ref
            
            elif hasattr(self.browser_view, 'canvas') and isinstance(self.browser_view.canvas, QtWidgets.QWidget):
                # Matplotlib Figure
                self.canvas = FigureCanvasQTAgg(self.browser_view)
                self.layout.addWidget(self.canvas)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout.addWidget(self.toolbar)
                self.canvas.draw()
            else:
                print(f"Unknown browser return type: {type(self.browser_view)}")
            
            # Focus logic
            if self.canvas:
                self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
                self.canvas.setFocus()

            
        except Exception as e:
            print(f"Error loading raw file: {e}")
            error_label = QtWidgets.QLabel(f"Error: {str(e)}")
            self.layout.addWidget(error_label)
            if self.canvas:
                self.canvas.deleteLater()
                self.canvas = None
