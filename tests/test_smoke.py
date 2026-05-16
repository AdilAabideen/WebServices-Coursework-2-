"""Smoke tests for the initial project scaffold.

Test type: smoke tests for importability and entry-point sanity.
"""

import importlib


# Smoke test for package imports successfully.
def test_package_imports_successfully() -> None:
    module = importlib.import_module("src")
    assert module is not None


# Smoke test for main module exposes main.
def test_main_module_exposes_main() -> None:
    module = importlib.import_module("src.main")
    assert callable(module.main)
