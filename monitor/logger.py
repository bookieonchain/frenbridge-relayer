from datetime import datetime
import json
import logging
import sys

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


cf = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")

file_handler = logging.FileHandler(filename="monitor.log")
file_handler.setFormatter(cf)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setFormatter(cf)
handlers = [file_handler, stdout_handler]
logger = logging

logging.basicConfig(
    level=logging.INFO,
    format="FRENMONITOR: [%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    handlers=handlers,
)
