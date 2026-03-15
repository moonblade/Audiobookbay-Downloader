"""
Test that all modules can be imported without errors.

This catches issues like undefined variables at module load time (e.g., issue #30).
"""

import sys
import importlib


def test_constants_import():
    """Test that constants.py imports without NameError or other exceptions."""
    # This would fail with: NameError: name 'ADMIN_USER' is not defined
    # if there are undefined variables at module level
    from abb import constants
    
    # Verify ADMIN_USER_DICT is properly defined
    assert constants.ADMIN_USER_DICT is not None
    assert constants.ADMIN_USER_DICT.username == "admin"
    assert constants.ADMIN_USER_DICT.role == "admin"


def test_all_modules_import():
    """Test that all core modules can be imported without errors."""
    modules = [
        "abb.models",
        "abb.constants",
        "abb.config_db",
        "abb.utils",
        "abb.db",
        "abb.audiobookbay",
        "abb.torrent",
        "abb.torrent_service",
        "abb.beetsapi",
        "abb.main",
    ]
    
    for module_name in modules:
        # This will raise if there are import-time errors like NameError
        module = importlib.import_module(module_name)
        assert module is not None, f"Failed to import {module_name}"


def test_app_can_be_created():
    """Test that the FastAPI app can be instantiated."""
    from abb.main import app
    
    assert app is not None
    # Verify it's a FastAPI app
    assert hasattr(app, "routes")
