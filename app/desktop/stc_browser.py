import mne
from PySide6 import QtWidgets, QtCore
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class StcBrowser(QtWidgets.QWidget):
    """
    Widget that displays Source Estimate (STC) time courses.
    """
    def __init__(self, title="Source Time Courses", parent=None):
        super().__init__(parent)
        self.title = title
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stc = None
        self.canvas = None
        self.figure = None
        self.toolbar = None
        
        # Placeholder Label
        self.placeholder = QtWidgets.QLabel("Select a Source Estimate (.stc) file to view traces")
        self.placeholder.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.placeholder)

    def load_stc(self, file_path):
        """Load an STC file and display its traces."""
        try:
            # Clear previous
            if self.canvas:
                self.layout.removeWidget(self.canvas)
                self.canvas.deleteLater()
                self.canvas = None
                self.figure = None
                plt.close('all') 

            if self.toolbar:
                self.layout.removeWidget(self.toolbar)
                self.toolbar.deleteLater()
                self.toolbar = None

            if self.placeholder.isVisible():
                self.placeholder.setVisible(False)

            print(f"Loading STC file: {file_path}")
            # Read STC
            self.stc = mne.read_source_estimate(file_path)
            
            # Create Plot
            self.figure = Figure(figsize=(8, 6), dpi=100)
            ax = self.figure.add_subplot(111)
            
            # Plot traces (Butterfly plot)
            # stc.data is (n_dipoles, n_times)
            # We transpose to plot, but for butterfly sometimes distinct lines are better
            # Times on X (stc.times), Data on Y
            ax.plot(self.stc.times, self.stc.data.T, linewidth=0.5, alpha=0.7)
            
            ax.set_title(self.title)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.grid(True)
            self.figure.tight_layout()

            # Embed
            self.canvas = FigureCanvasQTAgg(self.figure)
            self.layout.addWidget(self.canvas)
            
            # Toolbar
            self.toolbar = NavigationToolbar(self.canvas, self)
            self.layout.addWidget(self.toolbar)

            self.canvas.draw()
            
        except Exception as e:
            print(f"Error loading STC file: {e}")
            error_label = QtWidgets.QLabel(f"Error: {str(e)}")
            self.layout.addWidget(error_label)
            if self.canvas:
                self.canvas.deleteLater()
                self.canvas = None
