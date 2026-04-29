"""Model Selector — chooses AI model based on task complexity and API quota."""
import logging
import subprocess
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Keywords indicating complex tasks that need Opus
COMPLEX_KEYWORDS = [
    "multi-step", "analyze", "strategy", "negotiate", "complex",
    "cross-domain", "briefing", "financial", "reconcil", "dispute",
    "legal", "contract", "architecture", "refactor",
]

# Task types that are always routine (Sonnet)
ROUTINE_TYPES = [
    "email", "email_reply", "triage", "social_post", "status_update",
    "simple_draft", "acknowledgment", "schedule", "social", "invoice",
]


def load_model_config(config_path: Path) -> dict:
    """Load model configuration from agent YAML config.

    Args:
        config_path: Path to cloud-agent.yaml or local-agent.yaml.

    Returns:
        Dict with 'primary', 'complex', 'fallback' model strings.
    """
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return data.get("model_config", {
            "primary": "claude-sonnet-4-6",
            "complex": "claude-opus-4-6",
            "fallback": "minimax:m2.5:cloud",
        })
    except (OSError, yaml.YAMLError) as e:
        logger.error("Failed to load model config from %s: %s", config_path, e)
        return {
            "primary": "claude-sonnet-4-6",
            "complex": "claude-opus-4-6",
            "fallback": "minimax:m2.5:cloud",
        }


def assess_complexity(task_type: str, task_content: str) -> str:
    """Assess whether a task is routine or complex.

    Args:
        task_type: The type field from task YAML frontmatter.
        task_content: The full text content of the task file.

    Returns:
        'routine' or 'complex'.
    """
    if task_type in ROUTINE_TYPES:
        return "routine"

    content_lower = task_content.lower()
    for keyword in COMPLEX_KEYWORDS:
        if keyword in content_lower:
            return "complex"

    # Default to routine for token efficiency
    return "routine"


def check_api_quota_available() -> bool:
    """Check if Anthropic API quota is available.

    Attempts a minimal API call to verify quota.
    Returns True if API is accessible, False if quota exhausted.
    """
    try:
        result = subprocess.run(
            ["claude", "--print", "--max-turns", "1", "respond with OK"],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def select_model(
    config_path: Path,
    task_type: str = "",
    task_content: str = "",
    skip_quota_check: bool = False,
) -> str:
    """Select the appropriate AI model for a task.

    Decision flow:
    1. If paid API quota exhausted → fallback (Ollama)
    2. If task is complex → Opus
    3. Otherwise → Sonnet (token-efficient)

    Args:
        config_path: Path to agent YAML config file.
        task_type: Task type from frontmatter (e.g., 'email_reply').
        task_content: Full text content of the task.
        skip_quota_check: Skip API quota check (for testing).

    Returns:
        Model identifier string (e.g., 'claude-sonnet-4-6').
    """
    model_config = load_model_config(config_path)

    # Check API quota (unless skipped)
    if not skip_quota_check and not check_api_quota_available():
        logger.warning("API quota exhausted — using fallback model: %s", model_config["fallback"])
        return model_config["fallback"]

    # Assess complexity
    complexity = assess_complexity(task_type, task_content)

    if complexity == "complex":
        model = model_config["complex"]
        logger.info("Complex task detected — using model: %s", model)
    else:
        model = model_config["primary"]
        logger.debug("Routine task — using model: %s", model)

    return model
