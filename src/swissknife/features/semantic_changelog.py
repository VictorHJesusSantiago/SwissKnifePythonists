from __future__ import annotations

from dataclasses import dataclass

from swissknife.features.changelog import Commit, read_commits


@dataclass(slots=True)
class VersionBump:
    current: str
    next: str
    bump: str


def _parse_version(version: str) -> tuple[int, int, int]:
    parts = version.lstrip("v").split(".")
    major, minor, patch = (int(part) for part in (parts + ["0", "0", "0"])[:3])
    return major, minor, patch


def suggest_bump(commits: list[Commit]) -> str:
    if any(commit.breaking for commit in commits):
        return "major"
    if any(commit.subject.lower().startswith("feat") for commit in commits):
        return "minor"
    if commits:
        return "patch"
    return "none"


def next_version(current_version: str, commits: list[Commit]) -> VersionBump:
    bump = suggest_bump(commits)
    major, minor, patch = _parse_version(current_version)
    if bump == "major":
        major, minor, patch = major + 1, 0, 0
    elif bump == "minor":
        minor, patch = minor + 1, 0
    elif bump == "patch":
        patch += 1
    return VersionBump(current_version, f"{major}.{minor}.{patch}", bump)


def plan_release(current_version: str, revision_range: str = "", repo: str = ".") -> dict[str, object]:
    commits = read_commits(revision_range, repo)
    bump = next_version(current_version, commits)
    return {
        "current_version": bump.current,
        "next_version": bump.next,
        "bump": bump.bump,
        "commit_count": len(commits),
    }
