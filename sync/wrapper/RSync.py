import re
import subprocess

from sync.misc.Logger import logger

RSYNC_PATH = "/data/data/com.termux/files/usr/bin/rsync"

class RSync:

    def __init__(self, local_path, remote_path, port=22):
        self.local_path = str(local_path)
        self.remote_path = remote_path
        self.return_code = None
        self.port = port

    def get_command(self, duration=None, files=None, root=False, remote_root=False):
        command = []
        if root:
            command += ["sudo"]
        command += [RSYNC_PATH, "-ai"]
        if remote_root:
            command += ["--rsync-path='sudo rsync'"]
        if self.port != 22:
            command += ["-e", f"'ssh -p {self.port}'"]
        if duration is not None:
            newermt_arg = f"-newermt '{duration} seconds ago'"
            duration_arg = f"--files-from=<(cd {self.local_path} && find . {newermt_arg} -type f)"
            command += [duration_arg]
        elif files is not None:
            files_list = "\n".join(files)
            files_arg = f"--files-from=<(echo -e '{files_list}')"
            command += [files_arg]
        command += [self.local_path, self.remote_path]
        return command

    def run(self, duration=None, files=None, root=False, remote_root=False):
        command = self.get_command(duration, files, root, remote_root)

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
            #elif "error" in line.decode():
            #    yield "ERROR"
        self.return_code = process.poll()
        logger.print_sync_tool(f"Returned code: {self.return_code}")
