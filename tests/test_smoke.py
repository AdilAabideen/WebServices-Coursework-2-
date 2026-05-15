"""Smoke tests for the initial project scaffold."""

import importlib


def test_package_imports_successfully() -> None:
    module = importlib.import_module("src")
    assert module is not None


def test_main_module_exposes_main() -> None:
    module = importlib.import_module("src.main")
    assert callable(module.main)
