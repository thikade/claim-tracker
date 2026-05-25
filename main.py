"""Convenience launcher so you can run `python main.py` from the project root."""
from claim_tracker.app import run

if __name__ in {"__main__", "__mp_main__"}:
    run()
