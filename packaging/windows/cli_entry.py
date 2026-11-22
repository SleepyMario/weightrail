import sys

from weightrail.cli import main


if __name__ == "__main__":
    # Redirected Windows output otherwise uses a legacy code page.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
