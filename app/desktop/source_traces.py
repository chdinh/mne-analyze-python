from PySide6 import QtWidgets
from .stc_browser import StcBrowser

class SourceTracesWidget(QtWidgets.QWidget):
    """
    Container widget displaying stacked source trace browsers for LH and RH.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Left Hemisphere Browser
        self.browser_lh = StcBrowser(title="Left Hemisphere Source Traces")
        
        # Right Hemisphere Browser
        self.browser_rh = StcBrowser(title="Right Hemisphere Source Traces")
        
        self.layout.addWidget(self.browser_lh)
        self.layout.addWidget(self.browser_rh)
        
    def load_lh(self, path):
        self.browser_lh.load_stc(path)
        
    def load_rh(self, path):
        self.browser_rh.load_stc(path)
