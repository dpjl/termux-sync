import re
import subprocess

from sync.misc.Logger import logger

RSYNC_PATH = "/data/data/com.termux/files/usr/bin/rsync"

class RSync:

    def __init__(self, local_path, remote_path):
        self.local_path = local_path
        self.remote_path = remote_path
        self.return_code = None

    def get_command(self, duration=None, root=False):
        command = []
        if root:
            command += ["sudo"]
        command += [RSYNC_PATH, "-ai", "--rsync-path='sudo rsync'"]
        if duration is not None:
            newermt_arg = f"-newermt '{duration} seconds ago'"
            duration_arg = f"--files-from=<(cd {self.local_path} && find . {newermt_arg} -type f)"
            command += [duration_arg]
        command += [self.local_path, self.remote_path]
        return command

    def run(self, duration=None, root=False):
        command = self.get_command(duration, root)

        logger.print_sync_tool(f"Call: {' '.join(command)}")
        process = subprocess.Popen(' '.join(command),
                                   shell=True, executable='/data/data/com.termux/files/usr/bin/bash',
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            logger.print_sync_tool(line.decode().strip())
            match = re.search("<f.* (.*)", line.decode())
            if match:
                filename = match.group(1)
                yield filename
        self.return_code = process.poll()
        logger.print_sync_tool(f"Returned code: {self.return_code}")