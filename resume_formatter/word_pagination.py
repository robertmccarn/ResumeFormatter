from __future__ import annotations

import sys
from pathlib import Path

import win32com.client


def main() -> int:
    if len(sys.argv) != 2:
        print("Expected exactly one DOCX path.", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).resolve()
    word = None
    document = None

    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(
            str(path),
            ReadOnly=True,
            AddToRecentFiles=False,
        )
        document.Repaginate()
        # wdStatisticPages = 2.
        print(int(document.ComputeStatistics(2)))
        return 0
    except Exception as exc:
        print(f"Microsoft Word pagination failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
