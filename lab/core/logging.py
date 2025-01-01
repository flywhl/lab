import json
import logging.config
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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

def setup_logging(log_file: Optional[Path] = None) -> None:
    """Configure application logging from YAML file"""
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load config file
        config_path = Path(__file__).parent / "logging.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Substitute log file path
        os.environ["LOG_FILE"] = str(log_file)
        
        # Apply configuration
        logging.config.dictConfig(config)
    else:
        # If no log file specified, use null handler
        logger = logging.getLogger("lab")
        logger.addHandler(logging.NullHandler())
