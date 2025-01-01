import json
import logging.config
import os
from string import Template
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "context": getattr(record, "context", {}),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def load_logging_config(path: Path) -> dict:
    config_template = path.read_text()

    # Create a custom template with defaults
    template = Template(config_template)
    config_str = template.safe_substitute(
        {"_LOG_FILE_": os.getenv("LOG_FILE", "/var/log/default.log")}
    )

    return yaml.safe_load(config_str)


def setup_logging(log_file: Optional[Path] = None) -> None:
    """Configure application logging from YAML file"""
    if log_file:
        # Ensure log directory exists
        log_file = log_file.expanduser().resolve()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Load config file
        config_path = Path(__file__).parent / "logging.yaml"
        config = load_logging_config(config_path)

        # Set environment variable for template substitution
        os.environ["_LOG_FILE_"] = str(log_file)

        # Apply configuration
        logging.config.dictConfig(config)
    else:
        # If no log file specified, use null handler
        logger = logging.getLogger("lab")
        logger.addHandler(logging.NullHandler())
