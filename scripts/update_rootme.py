#!/usr/bin/env python3
"""
Pulls your Root-Me profile data from the official API and patches the
block between <!-- ROOTME:START --> and <!-- ROOTME:END --> in README.md.

Required environment variables (set as repo secrets):
  ROOTME_API_KEY  -> your Root-Me API key (or a valid spip_session cookie value)
  ROOTME_ID       -> your numeric id_auteur, found in your profile URL,
                     e.g. root-me.org/YourName-123456 -> ROOTME_ID=123456

NOTE: Root-Me's API is officially authenticated and the exact JSON shape
can shift over time. The first time you run this (locally or via
workflow_dispatch), check the printed raw_response in the logs and adjust
the field names below ("score", "rang", etc.) to match what comes back
for your account.
"""

import os
import re
import sys
import requests

API_KEY = os.environ.get("ROOTME_API_KEY")
USER_ID = os.environ.get("ROOTME_ID")
README_PATH = "README.md"

START_MARKER = "<!-- ROOTME:START -->"
END_MARKER = "<!-- ROOTME:END -->"


def fetch_profile():
    if not API_KEY or not USER_ID:
        print("Missing ROOTME_API_KEY or ROOTME_ID secrets.", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.www.root-me.org/auteurs/{USER_ID}"
    resp = requests.get(url, cookies={"api_key": API_KEY}, timeout=15)

    if resp.status_code != 200:
        print(f"Root-Me API returned {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    print("raw_response:", data)  # inspect this in the Actions log on first run
    return data


def build_block(data):
    score = data.get("score", "--")
    rank = data.get("position", "--")
  
    return (
        f"{START_MARKER}\n"
        "```\n"
        f"score        : {score}\n"
        f"rank         : {rank}\n"
        "last sync    : auto\n"
        "```\n"
        f"{END_MARKER}"
    )


def patch_readme(new_block):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL
    )

    if not pattern.search(content):
        print("Markers not found in README.md — nothing patched.", file=sys.stderr)
        sys.exit(1)

    new_content = pattern.sub(new_block, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    profile_data = fetch_profile()
    block = build_block(profile_data)
    patch_readme(block)
    print("README.md patched successfully.")
