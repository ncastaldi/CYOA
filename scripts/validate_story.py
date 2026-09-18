#!/usr/bin/env python3
"""Check a story file for parse and graph problems before it goes in the library.

Usage:
    python scripts/validate_story.py stories/example/story.md

For handing to a non-technical author: run this against whatever `story.md`
they send back, and read them the output rather than making them install
anything or boot the app. Requires the project's dependencies to be
installed (`pip install -e .` or `pip install -e ".[dev]"` from the repo
root) so that `cyoa` and `pyyaml` are importable.

Exit code is 0 if the story parses and has no blocking (ERROR-severity)
issues, 1 otherwise. Warnings are printed but do not affect the exit code.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cyoa.engine.graph import Severity, ValidationIssue, validate_story
from cyoa.engine.markdown_parser import MarkdownStoryParser
from cyoa.engine.parser import StoryParseError


def main() -> int:
    args = _parse_args()
    path = args.story_file

    if not path.is_file():
        print(f"No such file: {path}")
        return 1

    slug = path.parent.name
    source = path.read_text(encoding="utf-8")

    try:
        story = MarkdownStoryParser().parse(source, slug=slug)
    except StoryParseError as exc:
        print(f"Could not read this as a story at all:\n  {exc}")
        return 1

    issues = validate_story(story)
    errors = [issue for issue in issues if issue.severity is Severity.ERROR]
    warnings = [issue for issue in issues if issue.severity is Severity.WARNING]

    passage_count = len(story.passages)
    print(f'"{story.title}" — {passage_count} passage{"s" if passage_count != 1 else ""}')

    if errors:
        print(f"\n{len(errors)} problem{'s' if len(errors) != 1 else ''} to fix:")
        for issue in errors:
            _print_issue(issue)

    if warnings:
        print(f"\n{len(warnings)} thing{'s' if len(warnings) != 1 else ''} worth a look:")
        for issue in warnings:
            _print_issue(issue)

    if not issues:
        print("\nNo problems found. This story is ready to read.")

    return 1 if errors else 0


def _print_issue(issue: ValidationIssue) -> None:
    where = f" (passage: {issue.passage_id})" if issue.passage_id else ""
    print(f"  - {issue.message}{where}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("story_file", type=Path, help="Path to a story.md file")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
