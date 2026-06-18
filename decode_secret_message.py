"""Decode a secret message from a published Google Doc.

The Google Doc contains a table where each row specifies a Unicode
character and its (x, y) position in a 2D grid. When the grid is printed
in a fixed-width font, the characters form uppercase letters.

Coordinate system:
    - x increases to the right (column index).
    - y increases upward, so the row with the largest y is printed first
      (at the top) and y == 0 is printed last (at the bottom).
    - (0, 0) is the bottom-left corner.

Only the Python standard library is used, so no installation is required.
"""

import sys
from html.parser import HTMLParser
from urllib.request import urlopen, Request


class _TableCellParser(HTMLParser):
    """Collect the text content of every table cell, in document order."""

    def __init__(self):
        super().__init__()
        self._in_cell = False
        self._current = []
        self.cells = []

    def handle_starttag(self, tag, attrs):
        if tag in ("td", "th"):
            self._in_cell = True
            self._current = []

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self._in_cell = False
            self.cells.append("".join(self._current).strip())

    def handle_data(self, data):
        if self._in_cell:
            self._current.append(data)


def _fetch_html(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset)


def _parse_entries(html):
    """Return a list of (x, char, y) tuples parsed from the document table."""
    parser = _TableCellParser()
    parser.feed(html)
    cells = parser.cells

    entries = []
    # Cells come in groups of three: x-coordinate, character, y-coordinate.
    for i in range(0, len(cells) - 2, 3):
        x_raw, char, y_raw = cells[i], cells[i + 1], cells[i + 2]
        # Skip the header row (and anything else that isn't numeric).
        if not (x_raw.isdigit() and y_raw.isdigit()):
            continue
        entries.append((int(x_raw), char, int(y_raw)))
    return entries


def print_secret_message(url):
    """Fetch the Google Doc at `url`, parse the grid, and print the message."""
    html = _fetch_html(url)
    entries = _parse_entries(html)

    if not entries:
        return

    # Ensure the block-drawing characters print correctly on consoles that
    # default to a non-UTF-8 encoding (e.g. cp1252 on Windows).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    max_x = max(x for x, _, _ in entries)
    max_y = max(y for _, _, y in entries)

    grid = [[" "] * (max_x + 1) for _ in range(max_y + 1)]
    for x, char, y in entries:
        grid[y][x] = char

    # Largest y is the top row; y == 0 is the bottom row.
    for row in reversed(grid):
        print("".join(row))


if __name__ == "__main__":
    EXAMPLE_URL = (
        "https://docs.google.com/document/d/e/2PACX-1vTMOmshQe8YvaRXi6gEPKKlsC6"
        "UpFJSMAk4mQjLm_u1gmHdVVTaeh7nBNFBRlui0sTZ-snGwZM4DBCT/pub"
    )
    print_secret_message(EXAMPLE_URL)
