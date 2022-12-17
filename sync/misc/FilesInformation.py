from pathlib import Path

from sync.misc.Config import STATUS_LABELS, config
from sync.misc.Logger import logger
from sync.misc.Notification import Notification


class FilesInformation:

    def __init__(self, sync_name):
        self.sync_name = sync_name
        self.nb_files_sent = 0
        self.nb_files_updated = 0
        self.nb_unex_files_sent = 0
        self.new_files = []
        self.sent_files = []
        self.new_files_file = open(Path(config.workspace_path) / f"{self.sync_name}.txt", "a")
        self.status = "Started"

    def close(self):
        self.new_files_file.close()

    def get_status(self):
        files_status = f"{len(self.new_files)} > {self.nb_files_sent} [{self.nb_files_updated}]"
        return f"{STATUS_LABELS[self.status]} {files_status}"

    def synchronized_file(self, file_name):
        if file_name not in self.new_files:
            logger.print(f"Unexpected file {file_name}")
            self.nb_files_sent += 1
        else:
            if file_name not in self.sent_files:
                self.sent_files.append(file_name)
                self.nb_files_sent += 1
            else:
                self.nb_files_updated += 1
        logger.print(f"{self.nb_files_sent} sent / {self.nb_files_updated} upd / {self.nb_unex_files_sent} unex")
        Notification.get().update()

    def detected_file(self, file_path):
        file_name = Path(file_path).name
        if file_name not in self.new_files:
            logger.print_inotify(f"{file_name} modified in {self.sync_name}")
            self.status = "Work"
            self.new_files.append(file_name)
            self.new_files_file.write('\n'.join(self.new_files) + '\n')
            Notification.get().update()

    def sync_success_and_no_waiting_sync(self):
        self.status = "OK"
        Notification.get().update()

    def wait_connection(self):
        self.status = "Wait"
        Notification.get().update()

    def ready_connection(self):
        self.status = "Work"
