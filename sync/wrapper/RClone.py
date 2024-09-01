import re
import subprocess

from sync.misc.Logger import logger

RCLONE_PATH = "/data/data/com.termux/files/usr/bin/rclone"


class RClone:

    def __init__(self, local_path, remote_path, root=False, extra_options=[]):
        self.local_path = str(local_path)
        self.remote_path = remote_path
        self.return_code = None
        self.root = root
        self.extra_options = extra_options

    def get_command(self, duration=None, files=None, traverse=False):
        command = []
        if self.root:
            command += ["sudo"]
        command += [RCLONE_PATH, "copy", "-v"]
        if duration is not None:
            command += ["--max-age", f"{duration}s"]
        elif files is not None:
            files_list = "\n".join(files)
            files_arg = f"--files-from=<(echo -e '{files_list}')"
            command += [files_arg]
        if not traverse:
            command += ["--no-traverse"]
        command += self.extra_options
        command += [self.local_path, self.remote_path]
        return command

    def run(self, duration=None, files=None, traverse=False):
        command = self.get_command(duration, files, traverse)

        logger.print_sync_tool(f"Call: {' '.join(command)}")
        # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process = subprocess.Popen(' '.join(command),
                                   shell=True, executable='/data/data/com.termux/files/usr/bin/bash',
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
