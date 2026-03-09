#!/usr/bin/env python3
"""Update SHA256 hashes in toolchains/releases.bzl for dev/nightly releases.

Downloads each release artifact and computes its SHA256 hash, then rewrites
the releases.bzl file with updated shasum values.

Usage:
    python3 scripts/update-releases.py
"""

import hashlib
import re
import sys
import urllib.request
from pathlib import Path

RELEASES_FILE = Path(__file__).parent.parent / "toolchains" / "releases.bzl"

# Also support running from buck2 where __file__ is in buck-out
if not RELEASES_FILE.exists():
    RELEASES_FILE = Path("toolchains/releases.bzl")

# Match shasum lines: `"shasum": "...",`
SHASUM_RE = re.compile(r'^(\s*"shasum":\s*")[0-9a-f]*(",.*)$')

# Match url lines: `"url": "...",`
URL_RE = re.compile(r'"url":\s*"([^"]+)"')


def sha256_of_url(url: str) -> str:
    """Download a URL and return its SHA256 hex digest."""
    print(f"  Fetching {url.split('/')[-1]}...", end=" ", flush=True)
    with urllib.request.urlopen(url) as resp:
        h = hashlib.sha256()
        while chunk := resp.read(1 << 16):
            h.update(chunk)
    digest = h.hexdigest()
    print(digest[:16] + "...")
    return digest


def update_releases():
    content = RELEASES_FILE.read_text()
    lines = content.splitlines(keepends=True)

    # Build a map of url lines that follow shasum lines, keyed by line number
    # Strategy: for each shasum line, find the next url line (or vice versa)
    # Parse all URLs first
    url_by_line = {}
    for i, line in enumerate(lines):
        m = URL_RE.search(line)
        if m:
            url_by_line[i] = m.group(1)

    updated = 0
    new_lines = []
    for i, line in enumerate(lines):
        m = SHASUM_RE.match(line)
        if m:
            # Find the URL associated with this entry (next url line)
            url = None
            for j in range(i + 1, min(i + 5, len(lines))):
                if j in url_by_line:
                    url = url_by_line[j]
                    break
            # Also check preceding lines (url might come before shasum)
            if url is None:
                for j in range(max(0, i - 5), i):
                    if j in url_by_line:
                        url = url_by_line[j]
                        break

            if url:
                new_sha = sha256_of_url(url)
                line = m.group(1) + new_sha + m.group(2) + "\n"
                updated += 1

        new_lines.append(line)

    RELEASES_FILE.write_text("".join(new_lines))
    print(f"\nUpdated {updated} SHA256 hashes in {RELEASES_FILE}")


if __name__ == "__main__":
    print(f"Updating releases in {RELEASES_FILE}\n")
    try:
        update_releases()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
