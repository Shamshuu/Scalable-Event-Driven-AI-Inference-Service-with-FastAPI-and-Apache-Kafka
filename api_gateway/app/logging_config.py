import json
import logging
import sys
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname,
                "logger": record.name, "message": record.getMessage()}
        for key in ("request_id", "event"):
            if hasattr(record, key): data[key] = getattr(record, key)
        if record.exc_info: data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)

def configure_logging(level="INFO"):
    handler = logging.StreamHandler(sys.stdout); handler.setFormatter(JsonFormatter())
    root = logging.getLogger(); root.handlers = [handler]; root.setLevel(level)
