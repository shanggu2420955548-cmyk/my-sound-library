"""
Compatibility package for the personal fork layout.

The upstream code imports modules as ``transcriptionist_v3.*``. This fork keeps
the source folders at the repository root, so this package exposes the root as
part of ``transcriptionist_v3`` without renaming every module at once.
"""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__version__ = "3.0.0"
__author__ = "Transcriptionist Team"
__description__ = "Professional Sound Effects Management Platform"

_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

_project_root_str = str(_PROJECT_ROOT)
if _project_root_str not in __path__:
    __path__.append(_project_root_str)
