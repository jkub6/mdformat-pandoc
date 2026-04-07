import mdformat_pandoc
import sys

def test_version():
    print(f"\nVERSION DEBUG: {mdformat_pandoc.__file__}", file=sys.stderr)
