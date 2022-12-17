import datetime
import logging
import logging.config
import os
from pathlib import Path

import yaml

DEFAULT_CONF = """
version: 1
formatters:
  default:
    format: '%(message)s'
handlers:
{handler}
loggers:
  default:
    handlers: [handler]
    propagate: no
root:
  level: DEBUG
  handlers: [handler]
"""

HANDLER_CONSOLE = """
  handler:
    class: logging.StreamHandler
    level: {level}
    formatter: default
    stream: ext://sys.stdout
"""

HANDLER_FILE = """
  handler:
    level: {level}
    formatter: default
    class: logging.handlers.RotatingFileHandler
    filename: {log_file}
    mode: a
    maxBytes: 1048576
    backupCount: 10
"""


class Logger:
    def __init__(self):
        self.logger = None
        self.log_file = None

    def load(self, workspace_path, stdout, debug):
        self.log_file = (Path(workspace_path) / "termux-sync.log").absolute()

        if not os.path.exists(workspace_path):
            stdout = True

        level = "DEBUG" if debug else "INFO"
        handler_console = HANDLER_CONSOLE.format(level=level)
        handler_file = HANDLER_FILE.format(log_file=self.log_file, level=level)
        handler = handler_console if stdout else handler_file
        default_conf_yaml = DEFAULT_CONF.format(handler=handler)
        default_conf_dict = yaml.safe_load(default_conf_yaml)
        logging.config.dictConfig(default_conf_dict)
        self.logger = logging.getLogger('default')
        return True

    def print_line(self, content, prefix="", level="INFO"):
        if self.logger is not None:
            now_str = datetime.datetime.now().strftime('%Y-%m-%d@%H:%M:%S')
            if level == "INFO":
                self.logger.info(f"{prefix}{now_str}: {content}")
            elif level == "DEBUG":
                self.logger.debug(f"{prefix}{now_str}: {content}")

    def debug(self, content):
        self.print_line(content, level="DEBUG")

    def print(self, content):
        self.print_line(content)

    def print_inotify(self, content):
        self.print_line(content, "### ")

    def print_sync_tool(self, content):
        self.print_line(content, "--- ")


logger = Logger()
