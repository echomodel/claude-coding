"""Static analysis for claude-coding-plugin.

Validates that all skill references across the plugin resolve to actual
skills in the skills/ directory, and that all SKILL.md files have valid
frontmatter.

Run after ./build to verify the plugin is complete.
"""

import re
import yaml
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PLUGIN_ROOT / "skills"
AGENTS_DIR = PLUGIN_ROOT / "agents"


def get_skill_dirs():
    """Return set of skill names that exist in skills/."""
    return {
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    }


def parse_frontmatter(path):
    """Extract YAML frontmatter from a markdown file."""
    text = path.read_text()
    match = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


def find_md_files():
    """Find all .md files in the plugin, excluding vendored noise."""
    for p in PLUGIN_ROOT.rglob("*.md"):
        if ".git" in p.parts:
            continue
        yield p


# --- Tests ---


def test_all_skills_have_valid_frontmatter():
    """Every SKILL.md must have frontmatter with name and description."""
    errors = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        fm = parse_frontmatter(skill_md)
        if fm is None:
            errors.append(f"{skill_dir.name}: no frontmatter")
            continue
        if "name" not in fm:
            errors.append(f"{skill_dir.name}: missing 'name' in frontmatter")
        if "description" not in fm:
            errors.append(f"{skill_dir.name}: missing 'description' in frontmatter")
        if "name" in fm and fm["name"] != skill_dir.name:
            errors.append(
                f"{skill_dir.name}: frontmatter name '{fm['name']}' "
                f"does not match directory name"
            )
    assert not errors, "Frontmatter issues:\n" + "\n".join(f"  - {e}" for e in errors)


def test_agent_skill_references_resolve():
    """Every skill listed in agent frontmatter must exist in skills/."""
    available = get_skill_dirs()
    errors = []
    for agent_md in sorted(AGENTS_DIR.glob("*.md")):
        fm = parse_frontmatter(agent_md)
        if not fm or "skills" not in fm:
            continue
        for skill_name in fm["skills"]:
            if skill_name not in available:
                errors.append(f"{agent_md.name}: references '{skill_name}' but not in skills/")
    assert not errors, "Missing skills:\n" + "\n".join(f"  - {e}" for e in errors)


def test_claude_md_skill_references_resolve():
    """Skill names mentioned in CLAUDE.md should exist in skills/."""
    available = get_skill_dirs()
    claude_md = PLUGIN_ROOT / ".claude" / "CLAUDE.md"
    if not claude_md.exists():
        return

    text = claude_md.read_text()
    # Match backtick-wrapped skill names that look like skill references
    # e.g. `publish-pull-request`, `privacy-scan`
    refs = re.findall(r"`([a-z][a-z0-9-]+)`", text)
    # Filter to likely skill names (hyphenated, reasonable length)
    skill_like = {r for r in refs if "-" in r and len(r) > 4}

    missing = skill_like - available
    # Some backtick refs won't be skills — only flag ones that look like
    # they should be (match a known skill name pattern)
    known_non_skills = {
        "gh-pr-create", "git-push", "pre-publish", "non-negotiable",
        "squash-merge", "body-file",
    }
    missing -= known_non_skills

    if missing:
        # Warn, don't fail — heuristic matching can have false positives
        print(f"  Warning: CLAUDE.md references that may be missing skills: {missing}")


def test_build_cfg_skills_present():
    """Every skill listed in build.cfg should exist after build."""
    import configparser
    cfg = configparser.ConfigParser()
    cfg.read(PLUGIN_ROOT / "build.cfg")

    available = get_skill_dirs()
    errors = []

    for section in cfg.sections():
        skills_raw = cfg.get(section, "skills", fallback="")
        for line in skills_raw.strip().splitlines():
            skill_path = line.strip()
            if not skill_path:
                continue
            skill_name = Path(skill_path).name
            if skill_name not in available:
                errors.append(f"build.cfg [{section}]: '{skill_name}' not in skills/")

    assert not errors, "Build.cfg skills missing:\n" + "\n".join(f"  - {e}" for e in errors)


def test_no_empty_skill_directories():
    """Every directory in skills/ should have a SKILL.md."""
    empty = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if d.is_dir() and not (d / "SKILL.md").exists():
            empty.append(d.name)
    assert not empty, f"Empty skill directories: {empty}"
