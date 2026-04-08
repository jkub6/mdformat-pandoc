import sys

import mdformat_pandoc


def test_version():
    print(f"\nVERSION DEBUG: {mdformat_pandoc.__file__}", file=sys.stderr)
