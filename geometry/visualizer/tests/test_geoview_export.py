"""Backwards compatibility shim for test_geoview_export."""
from .test_visualizer_export import *

if __name__ == "__main__":
    import unittest
    unittest.main()
