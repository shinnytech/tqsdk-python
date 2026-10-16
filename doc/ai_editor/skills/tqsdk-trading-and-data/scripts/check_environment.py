"""Report the selected Python/TqSdk environment without installing or connecting."""

import contextlib
import importlib
import importlib.util
import io
import json
import platform
from pathlib import Path
import sys


def check_environment():
    result = {
        "python": platform.python_version(),
        "executable": sys.executable,
        "in_virtualenv": sys.prefix != sys.base_prefix,
    }
    if sys.version_info < (3, 9):
        return dict(result, status="python_too_old", minimum_python="3.9"), 3
    try:
        spec = importlib.util.find_spec("tqsdk")
        if spec is None:
            return dict(result, status="not_installed"), 1
        # Import only; never instantiate TqApi/TqAuth or inspect credentials.
        # TqSdk prints a notice on import; keep stdout machine-readable JSON.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sdk = importlib.import_module("tqsdk")
        if not getattr(sdk, "TqApi", None) or not getattr(sdk, "__version__", None):
            return dict(result, status="import_error", error_type="UnexpectedModule",
                        module_path=getattr(sdk, "__file__", None)), 2
        return dict(result, status="ready", tqsdk_version=sdk.__version__,
                    module_path=sdk.__file__), 0
    except Exception as exc:
        # Report type, not exception text: a user module could print sensitive data.
        return dict(result, status="import_error", error_type=type(exc).__name__), 2


if __name__ == "__main__":
    # Run from the user's project directory, as for a script saved there.
    sys.path.insert(0, str(Path.cwd()))
    report, exit_code = check_environment()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)
