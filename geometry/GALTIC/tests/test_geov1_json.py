"""Backwards compatibility shim for test_geov1_json."""
from .test_galtic_json import *

if __name__ == "__main__":
    import unittest
    unittest.main()
