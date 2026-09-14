import json, logging, sys
from datetime import datetime, timezone
class JsonFormatter(logging.Formatter):
    def format(self, record):
        item = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname, "logger": record.name, "message": record.getMessage()}
        for key in ("request_id", "event"):
            if hasattr(record, key): item[key] = getattr(record, key)
        if record.exc_info: item["exception"] = self.formatException(record.exc_info)
        return json.dumps(item)
def configure_logging(level="INFO"):
    stream = logging.StreamHandler(sys.stdout); stream.setFormatter(JsonFormatter())
    root = logging.getLogger(); root.handlers = [stream]; root.setLevel(level)
