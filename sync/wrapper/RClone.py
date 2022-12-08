import re
import subprocess

from sync.misc.Logger import logger

RCLONE_PATH = "/data/data/com.termux/files/usr/bin/rclone"


class RClone:

    def __init__(self, local_path, remote_path):
        self.local_path = local_path
        self.remote_path = remote_path
        self.return_code = None

    def get_command(self, duration=None, traverse=False, root=False):
        command = []
        if root:
            command += ["sudo"]
        command += [RCLONE_PATH, "copy", "-v"]
        if duration is not None:
            command += ["--max-age", f"{duration}s"]
        if not traverse:
            command += ["--no-traverse"]
        command += [self.local_path, self.remote_path]
        return command

    def run(self, duration=None, traverse=False, root=False):
        command = self.get_command(duration, traverse, root)

        logger.print_sync_tool(f"Call: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            logger.print_sync_tool(line.decode().strip())
            match = re.search(".*: (.*):.*", line.decode())
            if match:
                filename = match.group(1)
                yield filename
        self.return_code = process.poll()
        logger.print_sync_tool(f"Returned code: {self.return_code}")
