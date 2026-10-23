"""Module execution entry point for `python3 -m code_review_agent`."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
