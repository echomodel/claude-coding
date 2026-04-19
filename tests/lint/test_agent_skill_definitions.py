"""Lint checks for agent and skill definition files.

Validates source files in the repo have well-formed frontmatter and
consistent cross-references. No build step — the repo is the plugin.
"""

import json
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
SKILLS_DIR = REPO_ROOT / "skills"


def parse_frontmatter(path):
    text = path.read_text()
    match = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


def all_agent_files():
    if not AGENTS_DIR.is_dir():
        return []
    return sorted(AGENTS_DIR.glob("*.md"))


def all_skill_dirs():
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        s for s in SKILLS_DIR.iterdir()
        if s.is_dir() and (s / "SKILL.md").exists()
    )


# --- Agent frontmatter ---

@pytest.mark.parametrize("agent_file", all_agent_files(), ids=lambda p: p.stem)
def test_agent_has_valid_frontmatter(agent_file):
    fm = parse_frontmatter(agent_file)
    assert fm is not None, f"No frontmatter in {agent_file.name}"
    assert "name" in fm, f"Missing 'name' in {agent_file.name}"
    assert "description" in fm, f"Missing 'description' in {agent_file.name}"


# --- Skill frontmatter ---

@pytest.mark.parametrize("skill_dir", all_skill_dirs(), ids=lambda p: p.name)
def test_skill_has_valid_frontmatter(skill_dir):
    skill_md = skill_dir / "SKILL.md"
    fm = parse_frontmatter(skill_md)
    assert fm is not None, f"No frontmatter in {skill_dir.name}"
    assert "name" in fm, f"Missing 'name' in {skill_dir.name}"
    assert "description" in fm, f"Missing 'description' in {skill_dir.name}"
    assert fm["name"] == skill_dir.name, (
        f"Frontmatter name '{fm['name']}' doesn't match directory "
        f"'{skill_dir.name}'"
    )


# --- Plugin config files ---

@pytest.mark.parametrize("filename", [
    ".claude-plugin/plugin.json",
    "settings.json",
    "hooks/hooks.json",
    ".mcp.json",
])
def test_plugin_file_exists_and_valid(filename):
    path = REPO_ROOT / filename
    assert path.exists(), f"Missing {filename}"
    if filename.endswith(".json"):
        content = path.read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {filename}: {e}")


def test_settings_agent_ref_resolves():
    settings = json.loads((REPO_ROOT / "settings.json").read_text())
    agent_name = settings.get("agent")
    if not agent_name:
        pytest.skip("No agent in settings.json")
    path = AGENTS_DIR / f"{agent_name}.md"
    assert path.exists(), (
        f"settings.json references agent '{agent_name}' but not found in "
        f"agents/"
    )
