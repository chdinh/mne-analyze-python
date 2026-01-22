import sys
import os
import unittest

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stc_viewer.core.data import load_brain_data
from stc_viewer.core.state import AppState

class TestCore(unittest.TestCase):
    def test_state_initialization(self):
        state = AppState()
        self.assertEqual(state.visualization_mode, 0.0)
        self.assertTrue(state.show_traces)
        print("AppState initialized successfully.")

    def test_data_loading(self):
        print("Testing data loading (this might download files)...")
        data = load_brain_data()
        self.assertIn("vertices", data)
        self.assertIn("faces", data)
        self.assertEqual(data["vertices"].shape[1], 3)
        print(f"Loaded {len(data['vertices'])} vertices.")

if __name__ == "__main__":
    unittest.main()
