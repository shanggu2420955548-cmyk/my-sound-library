"""Development entry point for ``python -m transcriptionist_v3``."""

from __future__ import annotations

import importlib.util
import multiprocessing
import sys
from pathlib import Path
from types import ModuleType


def _load_root_entrypoint() -> ModuleType:
    root_main = Path(__file__).resolve().parent.parent / "__main__.py"
    spec = importlib.util.spec_from_file_location("transcriptionist_v3._root_entrypoint", root_main)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load root entry point: {root_main}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = _load_root_entrypoint()
    return int(module.run_cli())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if getattr(sys, "frozen", False) and len(sys.argv) >= 3 and sys.argv[1] == "-c":
        exec(compile(sys.argv[2], "<string>", "exec"))
        sys.exit(0)
    sys.exit(main())
