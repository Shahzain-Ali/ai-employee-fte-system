"""Gold tier scheduled jobs — CEO Briefing and audit retention."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def register_gold_jobs(scheduler, vault_path: Path) -> None:
    """Register Gold tier cron jobs with APScheduler.

    Args:
        scheduler: APScheduler instance.
        vault_path: Root path of the Obsidian vault.
    """
    # CEO Briefing: Every Sunday at 22:00
    scheduler.add_job(
        _run_ceo_briefing,
        "cron",
        day_of_week="sun",
        hour=22,
        minute=0,
        args=[vault_path],
        id="ceo_briefing_weekly",
        name="Weekly CEO Briefing",
        replace_existing=True,
    )
    logger.info("Scheduled: CEO Briefing (Sunday 22:00)")

    # Audit log retention: Daily at 03:00
    scheduler.add_job(
        _run_audit_retention,
        "cron",
        hour=3,
        minute=0,
        args=[vault_path],
        id="audit_retention_daily",
        name="Daily Audit Log Retention",
        replace_existing=True,
    )
    logger.info("Scheduled: Audit retention (daily 03:00)")


def _run_ceo_briefing(vault_path: Path) -> None:
    """Generate the weekly CEO Briefing."""
    try:
        from src.utils.ceo_briefing import CEOBriefingGenerator
        generator = CEOBriefingGenerator(vault_path=vault_path)
        path = generator.generate()
        logger.info("CEO Briefing generated: %s", path)
    except Exception as e:
        logger.error("CEO Briefing generation failed: %s", e)


def _run_audit_retention(vault_path: Path) -> None:
    """Run audit log retention cleanup."""
    try:
        from src.utils.audit_retention import cleanup_old_logs
        result = cleanup_old_logs(vault_path=vault_path, retention_days=90)
        if result["deleted_count"] > 0:
            logger.info("Audit retention: deleted %d files, freed %d bytes",
                        result["deleted_count"], result["total_size_freed"])
    except Exception as e:
        logger.error("Audit retention failed: %s", e)
