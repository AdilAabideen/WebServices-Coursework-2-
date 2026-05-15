"""Custom exceptions for the project domain."""

from __future__ import annotations


class ProjectError(Exception):
    """Base exception for project-specific failures."""


class CliUsageError(ProjectError):
    """Raised when CLI input is invalid."""


class CrawlError(ProjectError):
    """Raised when crawler configuration or execution is invalid."""


class DuplicateDocumentError(ProjectError):
    """Raised when multiple documents share the same identifier."""


class IndexStorageError(ProjectError):
    """Raised when index persistence or loading fails."""


class IndexValidationError(IndexStorageError):
    """Raised when an index payload has invalid or incomplete structure."""
