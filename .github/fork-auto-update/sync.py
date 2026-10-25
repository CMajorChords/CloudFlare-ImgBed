#!/usr/bin/env python3
"""Merge upstream main while retaining this fork's automation and local changes."""
import json
import os
import re
import subprocess


def git(*args, capture=False):
    return subprocess.run(
        ["git", *args], check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    )


def is_ancestor(commit, ref):
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, ref],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


git("config", "user.name", "github-actions[bot]")
git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
git("remote", "add", "upstream", f"https://github.com/{os.environ['UPSTREAM_REPO']}.git")
git("fetch", "--no-tags", "upstream", "main")

manifest_path = os.environ.get("BREAKING_MANIFEST_PATH")
if manifest_path:
    manifest = json.loads(git("show", f"upstream/main:{manifest_path}", capture=True).stdout)
    if manifest.get("schemaVersion") != 1 or not isinstance(manifest.get("updates"), list):
        raise SystemExit("Invalid upstream compatibility manifest; synchronization stopped.")
    pending = []
    for update in manifest["updates"]:
        if update.get("enabled") is False:
            continue
        introduced = update.get("introducedCommit") or ""
        if re.fullmatch(r"[0-9a-fA-F]{40}", introduced) and is_ancestor(introduced, "upstream/main") and is_ancestor(introduced, "HEAD"):
            continue
        pending.append(update["id"])
    if pending and os.environ.get("CONFIRM_BREAKING_UPDATE") != "true":
        raise SystemExit(
            "Compatibility update requires review: " + ", ".join(pending)
            + ". Read the upstream notice, then rerun this workflow with confirmation."
        )

git("merge", "--no-edit", "upstream/main")
git("push", "origin", "HEAD:main")
