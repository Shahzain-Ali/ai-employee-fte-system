"""Plan Manager — creates and manages Plan.md reasoning scratchpads for complex tasks."""
import logging
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone

from src.utils.logger import AuditLogger, LogEntry
from src.utils.dashboard import update_dashboard

logger = logging.getLogger(__name__)


class PlanManager:
    """Creates and manages PLAN_{slug}_{date}.md files in Plans/.

    Plans are Claude's reasoning artifacts for complex multi-step tasks.
    Each step can be marked complete, blocked, or require approval.

    Lifecycle: Complex task → Plan created → Steps executed → Plan complete
    """

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self._plans_dir = self.vault_path / "Plans"
        self._plans_dir.mkdir(exist_ok=True)
        self._audit = AuditLogger(vault_path=vault_path)

    def create_plan(
        self,
        task: str,
        steps: list[dict],
        source_file: str = "",
    ) -> Path:
        """Create a new PLAN_{slug}_{date}.md file.

        Args:
            task: Human-readable task description (e.g. "Invoice Client A — 50,000 PKR")
            steps: List of step dicts with keys:
                - description (str): What this step does
                - requires_approval (bool): Whether HITL approval needed
            source_file: Optional source action file that triggered this plan.

        Returns:
            Path to the created Plan.md file.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        entry_id = str(uuid.uuid4())
        slug = self._slugify(task)

        filename = f"PLAN_{slug}_{date_str}.md"
        plan_path = self._plans_dir / filename

        # Handle name collision
        if plan_path.exists():
            short_id = str(uuid.uuid4())[:6]
            filename = f"PLAN_{slug}_{date_str}_{short_id}.md"
            plan_path = self._plans_dir / filename

        requires_approval = any(s.get("requires_approval", False) for s in steps)

        # Build steps markdown
        steps_md = ""
        for i, step in enumerate(steps, 1):
            desc = step["description"]
            if step.get("requires_approval", False):
                steps_md += f"- [ ] {i}. {desc} ⚠️ REQUIRES APPROVAL\n"
            else:
                steps_md += f"- [ ] {i}. {desc}\n"

        content = f"""---
id: {entry_id}
type: plan
task: "{task}"
created_at: {iso_now}
updated_at: {iso_now}
status: in_progress
source_file: {source_file or "none"}
steps_total: {len(steps)}
steps_completed: 0
requires_approval: {str(requires_approval).lower()}
---

# Plan: {task}

## Steps

{steps_md.rstrip()}

## Notes

Plan created automatically. Steps will be executed sequentially.

## Blockers

None currently.
"""
        plan_path.write_text(content, encoding="utf-8")

        self._audit.log(LogEntry(
            action_type="plan_created",
            source="plan_manager",
            status="success",
            target_file=f"Plans/{filename}",
            details={
                "task": task,
                "steps_total": len(steps),
                "requires_approval": requires_approval,
                "source_file": source_file,
            },
        ))

        logger.info("Created plan: %s (%d steps)", filename, len(steps))
        return plan_path

    def add_step(self, plan_path: Path, description: str, requires_approval: bool = False) -> None:
        """Add a new step to an existing plan.

        Args:
            plan_path: Path to the Plan.md file.
            description: Step description.
            requires_approval: Whether this step needs HITL approval.
        """
        content = plan_path.read_text(encoding="utf-8")

        # Find the last step number
        step_numbers = re.findall(r"- \[[ x]\] (\d+)\.", content)
        next_num = int(step_numbers[-1]) + 1 if step_numbers else 1

        approval_tag = " ⚠️ REQUIRES APPROVAL" if requires_approval else ""
        new_step = f"- [ ] {next_num}. {description}{approval_tag}"

        # Insert before "## Notes"
        content = content.replace("## Notes", f"{new_step}\n\n## Notes")

        # Update steps_total in frontmatter
        content = self._update_frontmatter(content, "steps_total", str(next_num))
        if requires_approval:
            content = self._update_frontmatter(content, "requires_approval", "true")
        content = self._update_timestamp(content)

        plan_path.write_text(content, encoding="utf-8")
        logger.info("Added step %d to %s", next_num, plan_path.name)

    def mark_step_complete(self, plan_path: Path, step_number: int, note: str = "") -> None:
        """Mark a step as completed with timestamp.

        Args:
            plan_path: Path to the Plan.md file.
            step_number: 1-based step number to mark complete.
            note: Optional note to add after completion.
        """
        content = plan_path.read_text(encoding="utf-8")
        now_str = datetime.now(timezone.utc).strftime("%H:%M")

        # Replace the checkbox for this step
        pattern = rf"- \[ \] {step_number}\. (.+)"
        match = re.search(pattern, content)
        if not match:
            logger.warning("Step %d not found in %s", step_number, plan_path.name)
            return

        step_text = match.group(1)
        # Remove approval tag from completed step
        step_text = step_text.replace(" ⚠️ REQUIRES APPROVAL", "")
        replacement = f"- [x] {step_number}. {step_text} (completed {now_str})"
        content = content[:match.start()] + replacement + content[match.end():]

        # Add note if provided
        if note:
            notes_idx = content.find("## Notes")
            if notes_idx != -1:
                insert_pos = content.find("\n", notes_idx) + 1
                content = content[:insert_pos] + f"\n{note}\n" + content[insert_pos:]

        # Update steps_completed count
        completed = len(re.findall(r"- \[x\]", content))
        content = self._update_frontmatter(content, "steps_completed", str(completed))

        # Check if all done
        total_match = re.search(r"steps_total: (\d+)", content)
        total = int(total_match.group(1)) if total_match else 0
        if completed >= total:
            content = self._update_frontmatter(content, "status", "completed")
            logger.info("Plan %s completed!", plan_path.name)

        content = self._update_timestamp(content)
        plan_path.write_text(content, encoding="utf-8")
        logger.info("Step %d completed in %s", step_number, plan_path.name)

    def get_next_step(self, plan_path: Path) -> dict | None:
        """Get the next uncompleted step from a plan.

        Args:
            plan_path: Path to the Plan.md file.

        Returns:
            Dict with 'number', 'description', 'requires_approval' keys, or None if all done.
        """
        content = plan_path.read_text(encoding="utf-8")

        # Find first unchecked step
        match = re.search(r"- \[ \] (\d+)\. (.+)", content)
        if not match:
            return None

        step_num = int(match.group(1))
        description = match.group(2).strip()
        requires_approval = "REQUIRES APPROVAL" in description

        # Clean description
        description = description.replace(" ⚠️ REQUIRES APPROVAL", "").strip()

        return {
            "number": step_num,
            "description": description,
            "requires_approval": requires_approval,
        }

    def get_plan_status(self, plan_path: Path) -> dict:
        """Get the current status of a plan.

        Args:
            plan_path: Path to the Plan.md file.

        Returns:
            Dict with plan metadata and step progress.
        """
        content = plan_path.read_text(encoding="utf-8")

        task = self._read_frontmatter(content, "task") or ""
        status = self._read_frontmatter(content, "status") or "in_progress"
        total = int(self._read_frontmatter(content, "steps_total") or "0")
        completed = int(self._read_frontmatter(content, "steps_completed") or "0")

        return {
            "task": task.strip('"'),
            "status": status,
            "steps_total": total,
            "steps_completed": completed,
            "progress_pct": round((completed / total * 100) if total else 0),
            "file": plan_path.name,
        }

    def detect_approval_required(self, plan_path: Path) -> list[dict]:
        """Find all steps that require approval.

        Args:
            plan_path: Path to the Plan.md file.

        Returns:
            List of step dicts with 'number' and 'description'.
        """
        content = plan_path.read_text(encoding="utf-8")
        approval_steps = []

        for match in re.finditer(r"- \[ \] (\d+)\. (.+?)⚠️ REQUIRES APPROVAL", content):
            approval_steps.append({
                "number": int(match.group(1)),
                "description": match.group(2).strip(),
            })

        return approval_steps

    def get_active_plans(self) -> list[Path]:
        """Get all in-progress plans.

        Returns:
            List of plan file paths sorted by creation time (newest first).
        """
        plans = list(self._plans_dir.glob("PLAN_*.md"))
        active = []
        for p in plans:
            content = p.read_text(encoding="utf-8")
            if "status: in_progress" in content:
                active.append(p)

        active.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return active

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert task description to filename-safe slug."""
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s_]+", "_", slug)
        return slug[:40].strip("_")

    @staticmethod
    def _update_frontmatter(content: str, key: str, value: str) -> str:
        """Update a single frontmatter field value."""
        pattern = rf"({key}: ).+"
        return re.sub(pattern, rf"\g<1>{value}", content, count=1)

    @staticmethod
    def _update_timestamp(content: str) -> str:
        """Update the updated_at timestamp in frontmatter."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return re.sub(r"(updated_at: ).+", rf"\g<1>{now}", content, count=1)

    @staticmethod
    def _read_frontmatter(content: str, key: str) -> str | None:
        """Read a single frontmatter field value."""
        match = re.search(rf"{key}: (.+)", content)
        return match.group(1).strip() if match else None
