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
            
            # Create plot
            # MNE plot returning a figure. 
            # Note: For efficient browsing, MNE usually opens a new window in 'qt' mode.
            # To embed, we need to ask MNE to plot to a specific figure or capture it.
            # However, mne.Viz raw.plot usually returns a Figure object if show=False.
            # Let's try standard matplotlib embedding.
            
            # We use the 'agg' backend for MNE to ensure it generates a Figure we can embed, 
            # but usually we need 'qtagg' for interactivity in Qt.
            # MNE's raw.plot is complex. 
            
            # Option 1: Use mne.viz.plot_raw with show=False
            fig = self.raw.plot(show=False, block=False, duration=10.0, start=0.0)
            
            # The returned object from raw.plot depends on the backend.
            # If using 'matplotlib' backend: returns matplotlib.figure.Figure
            # If using 'qt' backend (mne-qt-browser): returns a specific browser instance.
            
            # We assume default matplotlib backend for now as per plan.
            self.figure = fig
            
            # Embed
            # Note: If fig is already a MNEQtBrowser, we might need different handling.
            # Assuming it is a matplotlib figure:
            if hasattr(fig, 'canvas'):
                # It might already have a canvas, or we need to put it in a FigureCanvasQTAgg
                # If it's a standard MP figure, we wrap it.
                if isinstance(fig, Figure):
                     self.canvas = FigureCanvasQTAgg(fig)
                else:
                    # It might be the mne-qt-browser widget itself or similar
                    # Check if it is a widget
                    if isinstance(fig, QtWidgets.QWidget):
                        self.canvas = fig
                    elif hasattr(fig, 'canvas') and isinstance(fig.canvas, QtWidgets.QWidget):
                         self.canvas = fig.canvas
                    else:
                        # Fallback for standard matplotlib figure that needs a canvas
                        self.canvas = FigureCanvasQTAgg(fig)
            else:
                 self.canvas = FigureCanvasQTAgg(fig)

            self.layout.addWidget(self.canvas)
            
            # Create and add toolbar using the canvas
            if isinstance(self.canvas, FigureCanvasQTAgg):
                 self.toolbar = NavigationToolbar(self.canvas, self)
                 self.layout.addWidget(self.toolbar)

            self.canvas.draw()
            
        except Exception as e:
            print(f"Error loading raw file: {e}")
            error_label = QtWidgets.QLabel(f"Error: {str(e)}")
            self.layout.addWidget(error_label)
            if self.canvas:
                self.canvas.deleteLater()
                self.canvas = None
