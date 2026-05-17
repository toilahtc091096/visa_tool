"""Backward-compatible entrypoint; prefer running `python main.py`."""

from main import main, run_flow

__all__ = ["main", "run_flow"]

if __name__ == "__main__":
    main()
