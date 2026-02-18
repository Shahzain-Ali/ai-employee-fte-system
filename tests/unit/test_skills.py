"""T039/T040: Unit tests for Agent Skill file validation."""
import pytest
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent.parent / ".claude" / "skills"
REQUIRED_SKILLS = ["process_document.md", "update_dashboard.md", "create_approval_request.md"]
REQUIRED_SECTIONS = ["## Purpose", "## Steps", "## Output", "## Error Handling", "## Logging"]


def test_all_required_skills_exist():
    """All 3 required Agent Skills must exist in .claude/skills/."""
    for skill_name in REQUIRED_SKILLS:
        skill_path = SKILLS_DIR / skill_name
        assert skill_path.exists(), f"Missing required skill: {skill_name}"


@pytest.mark.parametrize("skill_name", REQUIRED_SKILLS)
def test_skill_has_required_sections(skill_name: str):
    """Each skill must contain all required sections."""
    skill_path = SKILLS_DIR / skill_name
    content = skill_path.read_text()
    for section in REQUIRED_SECTIONS:
        assert section in content, f"{skill_name} is missing section: {section}"


@pytest.mark.parametrize("skill_name", REQUIRED_SKILLS)
def test_skill_has_purpose(skill_name: str):
    """Each skill must have a non-empty Purpose section."""
    skill_path = SKILLS_DIR / skill_name
    content = skill_path.read_text()
    purpose_idx = content.find("## Purpose")
    steps_idx = content.find("## Steps")
    purpose_text = content[purpose_idx:steps_idx].strip()
    # Purpose section should have content beyond just the header
    assert len(purpose_text) > 20, f"{skill_name} Purpose section is too short"


def test_process_document_skill_references_logging():
    """process_document skill must reference Logs/YYYY-MM-DD.json."""
    content = (SKILLS_DIR / "process_document.md").read_text()
    assert "Logs/" in content


def test_create_approval_references_pending_approval():
    """create_approval_request skill must reference Pending_Approval/."""
    content = (SKILLS_DIR / "create_approval_request.md").read_text()
    assert "Pending_Approval" in content


def test_create_approval_references_hitl():
    """create_approval_request skill must reference HITL or approval workflow."""
    content = (SKILLS_DIR / "create_approval_request.md").read_text()
    assert "Approved" in content and "Rejected" in content
