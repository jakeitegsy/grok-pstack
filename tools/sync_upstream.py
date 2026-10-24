#!/usr/bin/env python3
"""Pin cursor/plugins pstack and merge it onto this Grok tree.

Files the harness has not touched are replaced with upstream.
Files both sides changed are a three-way merge from the last pin.
New text files get the harness token rewrite.
"""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = ROOT / "UPSTREAM_SHA"

REPLACEMENTS = (
    ("~/.cursor/rules/pstack-models.mdc", "~/.grok/rules/pstack-models.md"),
    ("the Task tool", "`spawn_subagent`"),
    ("Task tool", "`spawn_subagent`"),
    ("`Task`", "`spawn_subagent`"),
    ("grok-4.7-xhigh-fast", "grok-4.6"),
    ("claude-opus-4-8-xhigh", "grok-4.6"),
    ("claude-opus-5-5-xhigh", "grok-4.6"),
    ("claude-opus-4-6", "grok-4.6"),
    ("claude-4.6-sonnet", "grok-4.5"),
    ("subagent_type: generalPurpose", "omit `subagent_type`"),
    ('environment: "cloud"', 'isolation: "worktree"'),
    ('environment: "local"', 'isolation: "none"'),
)


def git_bytes(repo, sha, path):
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{path}"],
        cwd=repo,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    show = subprocess.run(
        ["git", "show", f"{sha}:{path}"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return show.stdout


def list_files(repo, sha):
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", sha, "pstack"],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    return [line[len("pstack/") :] for line in out.splitlines() if line.startswith("pstack/")]


def as_text(data):
    if data is None or b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def rewrite(text):
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="/tmp/cursor-plugins")
    parser.add_argument("--to", required=True)
    args = parser.parse_args()
    repo = args.repo
    base = PIN_FILE.read_text().strip()
    target = args.to
    conflicts = []
    updated = 0
    for rel in list_files(repo, target):
        dest = ROOT / rel
        new_b = git_bytes(repo, target, f"pstack/{rel}")
        old_b = git_bytes(repo, base, f"pstack/{rel}")
        new_t = as_text(new_b)
        old_t = as_text(old_b)
        if new_t is None:
            if not dest.exists() or dest.read_bytes() != new_b:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(new_b)
                updated += 1
            continue
        if dest.exists() and old_t is not None and dest.read_text() == old_t:
            dest.write_text(new_t)
            updated += 1
            continue
        if old_t is None and dest.exists():
            raise SystemExit(f"missing base blob for existing file {rel}")
        if old_t is None or not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(rewrite(new_t))
            updated += 1
            continue
        if new_t == old_t:
            continue
        merged = subprocess.run(
            ["git", "merge-file", "-p", "-", "-", "-"],
            input=None,
            capture_output=True,
        )
        # merge-file wants files. Write temps.
        base_path = Path("/tmp/sync-base")
        ours_path = Path("/tmp/sync-ours")
        theirs_path = Path("/tmp/sync-theirs")
        base_path.write_text(old_t)
        ours_path.write_text(dest.read_text())
        theirs_path.write_text(new_t)
        merged = subprocess.run(
            ["git", "merge-file", "-p", str(ours_path), str(base_path), str(theirs_path)],
            text=True,
            capture_output=True,
        )
        dest.write_text(rewrite(merged.stdout))
        updated += 1
        if merged.returncode != 0:
            conflicts.append(rel)
    PIN_FILE.write_text(target + "\n")
    print(f"updated {updated} files to {target[:12]}")
    if conflicts:
        print("conflicts:")
        for rel in conflicts:
            print(rel)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
