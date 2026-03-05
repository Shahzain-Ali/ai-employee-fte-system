"""Cross-domain workflow engine — orchestrates multi-domain actions."""
import uuid
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field

from src.utils.logger import AuditLogger, LogEntry

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """A single step in a cross-domain workflow."""
    domain: str
    action: str
    params: dict = field(default_factory=dict)
    status: str = "pending"  # pending, completed, failed, skipped
    result: str = ""
    error: str = ""
    duration_ms: int = 0


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution."""
    workflow_id: str
    status: str  # completed, partial_failure, failed
    steps: list[WorkflowStep] = field(default_factory=list)
    completed_count: int = 0
    failed_count: int = 0


class WorkflowEngine:
    """Executes multi-domain workflows with shared workflow_id and partial failure handling.

    Each workflow generates a unique workflow_id that links all actions
    across domains in the audit log for full traceability.

    Args:
        vault_path: Root path of the Obsidian vault.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self._audit = AuditLogger(vault_path=vault_path)

    def start_workflow(self, trigger: str, steps: list[WorkflowStep]) -> WorkflowResult:
        """Execute a cross-domain workflow.

        Steps are executed sequentially. Completed steps are preserved on failure.
        A notification file is created on any step failure.

        Args:
            trigger: Description of what triggered this workflow.
            steps: Ordered list of workflow steps to execute.

        Returns:
            WorkflowResult with status and step details.
        """
        workflow_id = f"wf-{uuid.uuid4().hex[:12]}"

        self._audit.log(LogEntry(
            action_type="workflow_started",
            source="workflow_engine",
            status="success",
            workflow_id=workflow_id,
            details={"trigger": trigger, "step_count": len(steps)},
        ))

        logger.info("Workflow %s started: %s (%d steps)", workflow_id, trigger, len(steps))

        result = WorkflowResult(workflow_id=workflow_id, status="completed", steps=steps)

        for i, step in enumerate(steps):
            start_time = time.time()
            try:
                step_result = self._execute_step(step, workflow_id)
                step.status = "completed"
                step.result = step_result
                step.duration_ms = int((time.time() - start_time) * 1000)
                result.completed_count += 1

                self._audit.log(LogEntry(
                    action_type=f"{step.domain}_{step.action}_completed",
                    source="workflow_engine",
                    status="success",
                    workflow_id=workflow_id,
                    domain=step.domain,
                    duration_ms=step.duration_ms,
                    details={"step": i + 1, "result_preview": step_result[:200]},
                ))

                logger.info("Workflow %s step %d/%d completed: %s.%s",
                            workflow_id, i + 1, len(steps), step.domain, step.action)

            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                step.duration_ms = int((time.time() - start_time) * 1000)
                result.failed_count += 1

                self._audit.log(LogEntry(
                    action_type=f"{step.domain}_{step.action}_failed",
                    source="workflow_engine",
                    status="failure",
                    workflow_id=workflow_id,
                    domain=step.domain,
                    duration_ms=step.duration_ms,
                    error_message=str(e),
                    details={"step": i + 1},
                ))

                logger.error("Workflow %s step %d/%d failed: %s.%s — %s",
                             workflow_id, i + 1, len(steps), step.domain, step.action, e)

                # Mark remaining steps as skipped
                for remaining in steps[i + 1:]:
                    remaining.status = "skipped"

                # Create notification
                self._create_failure_notification(workflow_id, trigger, step, i + 1, len(steps))
                break

        # Determine overall status
        if result.failed_count == 0:
            result.status = "completed"
        elif result.completed_count > 0:
            result.status = "partial_failure"
        else:
            result.status = "failed"

        self._audit.log(LogEntry(
            action_type=f"workflow_{result.status}",
            source="workflow_engine",
            status="success" if result.status == "completed" else "failure",
            workflow_id=workflow_id,
            details={
                "trigger": trigger,
                "completed": result.completed_count,
                "failed": result.failed_count,
                "total": len(steps),
            },
        ))

        return result

    def _execute_step(self, step: WorkflowStep, workflow_id: str) -> str:
        """Execute a single workflow step by creating an action file.

        The actual MCP invocation happens through the orchestrator's normal
        file-based flow. This method creates the appropriate action file
        in Needs_Action/ for the orchestrator to pick up.

        Args:
            step: The workflow step to execute.
            workflow_id: The parent workflow ID.

        Returns:
            Status message.
        """
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%dT%H%M%SZ")
        iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        prefix_map = {
            "odoo": "ODOO",
            "facebook": "FB",
            "instagram": "IG",
            "twitter": "TW",
            "linkedin": "LI",
            "email": "EMAIL",
        }
        prefix = prefix_map.get(step.domain, step.domain.upper())
        filename = f"{prefix}_{step.action}_{ts}.md"

        needs_action = self.vault_path / "Needs_Action"
        needs_action.mkdir(exist_ok=True)

        # Build action file content
        params_yaml = "\n".join(f"  {k}: {v}" for k, v in step.params.items())
        content = f"""---
type: {step.domain}
action: {step.action}
workflow_id: {workflow_id}
status: pending
created_at: {iso_now}
params:
{params_yaml}
---

# Cross-Domain Workflow Step

**Workflow**: {workflow_id}
**Domain**: {step.domain}
**Action**: {step.action}

## Parameters

{chr(10).join(f'- **{k}**: {v}' for k, v in step.params.items())}
"""
        action_path = needs_action / filename
        action_path.write_text(content, encoding="utf-8")

        return f"Action file created: {filename}"

    def _create_failure_notification(self, workflow_id: str, trigger: str,
                                     failed_step: WorkflowStep, step_num: int,
                                     total_steps: int) -> None:
        """Create a notification file for workflow failure.

        Args:
            workflow_id: The workflow ID.
            trigger: What triggered the workflow.
            failed_step: The step that failed.
            step_num: Which step number failed.
            total_steps: Total steps in the workflow.
        """
        needs_action = self.vault_path / "Needs_Action"
        needs_action.mkdir(exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"NOTIFICATION_workflow_failed_{ts}.md"
        content = f"""---
type: notification
severity: critical
workflow_id: {workflow_id}
created_at: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
---

# Workflow Failed

**Workflow ID**: {workflow_id}
**Trigger**: {trigger}
**Failed at step**: {step_num}/{total_steps}
**Domain**: {failed_step.domain}
**Action**: {failed_step.action}
**Error**: {failed_step.error}

## Suggested Action

Review the error above and retry the workflow, or complete remaining steps manually.
"""
        (needs_action / filename).write_text(content, encoding="utf-8")
