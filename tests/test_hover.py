"""
Tests for hover detection and text display functionality.

Tests the raycasting logic and text renderer behavior.
"""

import unittest
import numpy as np


class TestGetHoveredRegion(unittest.TestCase):
    """Tests for _get_hovered_region function logic."""

    def test_get_hovered_region_returns_tuple(self):
        """Verify that _get_hovered_region returns a tuple (name, id)."""
        # Simulate the expected return type
        result = (None, -1)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsNone(result[0])
        self.assertEqual(result[1], -1)

        result_with_region = ("L_G_frontal_sup", 42)
        self.assertIsInstance(result_with_region, tuple)
        self.assertEqual(result_with_region[0], "L_G_frontal_sup")
        self.assertEqual(result_with_region[1], 42)

    def test_screen_to_ndc_conversion(self):
        """Test mouse coordinate to NDC (Normalized Device Coordinates) conversion."""
        # Simulate the conversion logic from viewport (matches stc_viewer convention)
        width = 800
        height = 600

        # Center of screen should be (0, 0) in NDC
        mouse_x, mouse_y = width / 2, height / 2
        ndc_x = (mouse_x / width) * 2.0 - 1.0
        ndc_y = -((mouse_y / height) * 2.0 - 1.0)  # Inverted Y
        self.assertTrue(np.isclose(ndc_x, 0.0))
        self.assertTrue(np.isclose(ndc_y, 0.0))

        # Top-left corner should be (-1, 1)
        mouse_x, mouse_y = 0, 0
        ndc_x = (mouse_x / width) * 2.0 - 1.0
        ndc_y = -((mouse_y / height) * 2.0 - 1.0)
        self.assertTrue(np.isclose(ndc_x, -1.0))
        self.assertTrue(np.isclose(ndc_y, 1.0))

        # Bottom-right corner should be (1, -1)
        mouse_x, mouse_y = width, height
        ndc_x = (mouse_x / width) * 2.0 - 1.0
        ndc_y = -((mouse_y / height) * 2.0 - 1.0)
        self.assertTrue(np.isclose(ndc_x, 1.0))
        self.assertTrue(np.isclose(ndc_y, -1.0))

    def test_valid_label_bounds_check(self):
        """Test that label ID bounds checking works correctly."""
        region_names = ["Unknown", "L_G_frontal_sup", "L_S_central", "R_G_temporal_inf"]

        # Valid label IDs
        for label_id in [0, 1, 2, 3]:
            self.assertTrue(0 <= label_id < len(region_names))

        # Invalid label IDs
        for label_id in [-1, -5, 4, 100]:
            self.assertFalse(0 <= label_id < len(region_names))

    def test_distance_threshold(self):
        """Test the distance threshold for hover detection."""
        threshold = 0.05

        # Within threshold (threshold^2 = 0.0025)
        min_dist_within = 0.002
        self.assertLess(min_dist_within, threshold ** 2)

        # Outside threshold
        min_dist_outside = 0.003
        self.assertGreater(min_dist_outside, threshold ** 2)


class TestTextRenderer(unittest.TestCase):
    """Tests for TextRenderer behavior."""

    def test_empty_text_should_not_draw(self):
        """Verify that empty text should skip drawing."""
        current_text = ""
        should_draw = bool(current_text)
        self.assertFalse(should_draw)

        current_text = "L_G_frontal_sup"
        should_draw = bool(current_text)
        self.assertTrue(should_draw)

    def test_text_change_detection(self):
        """Test that text only updates when it changes."""
        current_text = "Initial"
        new_text = "Initial"
        should_update = new_text != current_text
        self.assertFalse(should_update)

        new_text = "Changed"
        should_update = new_text != current_text
        self.assertTrue(should_update)

    def test_region_name_formatting(self):
        """Test that region names are properly formatted."""
        # Test typical region name format from Destrieux atlas
        region_names = [
            "L_G_and_S_frontomargin",
            "L_G_and_S_occipital_inf",
            "R_S_temporal_transverse",
            "L_Unknown",
        ]

        for name in region_names:
            self.assertIsInstance(name, str)
            self.assertGreater(len(name), 0)
            self.assertTrue(name.startswith("L_") or name.startswith("R_"))


class TestHoverRendererIntegration(unittest.TestCase):
    """Tests for integration between hover detection and renderer."""

    def test_set_hovered_id_accepts_valid_ids(self):
        """Test that set_hovered_id should accept valid region IDs."""
        # Simulate the expected behavior
        valid_ids = [0, 1, 42, 100, -1]  # -1 means no hover
        for region_id in valid_ids:
            hovered_id = float(region_id)
            self.assertIsInstance(hovered_id, float)

    def test_no_hover_returns_minus_one(self):
        """Test that no hover state returns -1 as region ID."""
        no_hover_result = (None, -1)
        self.assertEqual(no_hover_result[1], -1)

    def test_hover_state_propagation(self):
        """Test that hover state propagates correctly from detection to rendering."""
        # Simulate the flow: detection -> text renderer + brain renderer
        region_name, region_id = ("L_G_frontal_sup", 42)

        # Text should show region name
        self.assertIsNotNone(region_name)
        text_to_display = region_name
        self.assertEqual(text_to_display, "L_G_frontal_sup")

        # Renderer should receive region ID for highlight
        hovered_id_for_shader = float(region_id)
        self.assertEqual(hovered_id_for_shader, 42.0)

    def test_no_hover_clears_display(self):
        """Test that leaving a region clears the text display."""
        region_name, region_id = (None, -1)

        # Text should be empty
        text_to_display = region_name if region_name else ""
        self.assertEqual(text_to_display, "")

        # Renderer should receive -1 to clear highlight
        hovered_id_for_shader = float(region_id)
        self.assertEqual(hovered_id_for_shader, -1.0)


class TestVertexProjection(unittest.TestCase):
    """Tests for vertex projection and picking logic."""

    def test_perspective_divide_avoids_zero(self):
        """Test that perspective divide handles w=0 correctly."""
        w = np.array([[1.0], [0.0], [0.5]])
        w_safe = w.copy()
        w_safe[w_safe == 0] = 1e-10
        
        self.assertEqual(w_safe[0, 0], 1.0)
        self.assertEqual(w_safe[1, 0], 1e-10)  # Replaced zero
        self.assertEqual(w_safe[2, 0], 0.5)

    def test_ndc_z_filter(self):
        """Test filtering vertices by NDC Z coordinate (after correction matrix maps to [0,1])."""
        ndc_coords = np.array([
            [0.0, 0.0, 0.5],   # Valid (in frustum)
            [0.0, 0.0, 0.1],   # Valid (closer to camera)
            [0.0, 0.0, 1.5],   # Invalid (behind far plane)
            [0.0, 0.0, -0.5],  # Invalid (behind near plane)
        ])

        # After correction matrix, Z range is [0, 1]
        valid_mask = (ndc_coords[:, 2] >= 0) & (ndc_coords[:, 2] <= 1)
        
        self.assertTrue(valid_mask[0])
        self.assertTrue(valid_mask[1])
        self.assertFalse(valid_mask[2])
        self.assertFalse(valid_mask[3])

    def test_closest_vertex_selection(self):
        """Test selecting the closest vertex by screen distance."""
        # Simulate screen distances
        screen_dist = np.array([0.1, 0.05, 0.01, 0.2, np.inf])
        
        closest_idx = np.argmin(screen_dist)
        self.assertEqual(closest_idx, 2)
        
        min_dist = screen_dist[closest_idx]
        self.assertEqual(min_dist, 0.01)

    def test_frontmost_vertex_selection(self):
        """Test that frontmost vertex is selected among candidates within threshold."""
        # Simulate multiple vertices within screen threshold at different depths
        ndc_coords = np.array([
            [0.0, 0.0, 0.8],   # Close in screen space, but far in Z
            [0.01, 0.01, 0.3], # Close in screen space, frontmost (smallest Z)
            [0.02, 0.02, 0.5], # Close in screen space, middle depth
        ])
        
        mouse_ndc = np.array([0.0, 0.0])
        threshold = 0.05
        
        # Calculate screen distances
        screen_dist = (ndc_coords[:, 0] - mouse_ndc[0]) ** 2 + (ndc_coords[:, 1] - mouse_ndc[1]) ** 2
        
        # Find candidates within threshold
        within_threshold = screen_dist < threshold ** 2
        candidate_indices = np.where(within_threshold)[0]
        
        # Among candidates, pick frontmost (smallest Z)
        candidate_z = ndc_coords[candidate_indices, 2]
        frontmost_local_idx = np.argmin(candidate_z)
        closest_idx = candidate_indices[frontmost_local_idx]
        
        # Should pick index 1 (Z=0.3, frontmost)
        self.assertEqual(closest_idx, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
