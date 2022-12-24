from pathlib import Path
from threading import Lock

from sync.misc.Config import STATUS_LABELS
from sync.misc.Logger import logger
from sync.misc.Notification import Notification


class FilesInformation:

    def __init__(self, sync_name):
        self.sync_name = sync_name
        self.nb_files_sent = 0
        self.nb_files_updated = 0
        self.nb_unex_files_sent = 0
        self.detected_files = []
        self.detected_files_history = []
        self.sent_files = []
        self.status = "Started"
        self.lock = Lock()

    def close(self):
        pass

    def get_status(self):
        files_status = f"{len(self.detected_files_history)} > {self.nb_files_sent} [{self.nb_files_updated}]"
        return f"{STATUS_LABELS[self.status]} {files_status}"

    def synchronized_file(self, file_name):
        if file_name not in self.detected_files_history:
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

    def detected_file(self, file_path: Path):
        file_name = file_path.name
        file_path_str = str(file_path)
        if file_path_str not in self.detected_files:
            logger.print_inotify(f"{file_path_str} creation/change detected in {self.sync_name}")
            self.status = "Work"
            with self.lock:
                self.detected_files.append(file_path_str)
            if file_name not in self.detected_files_history:
                self.detected_files_history.append(file_name)
            Notification.get().update()

    def get_next_files_to_sync(self):
        with self.lock:
            result = self.detected_files.copy()
            self.detected_files.clear()
        return result

    def cancel_sync(self, detected_files):
        with self.lock:
            self.detected_files += detected_files

    def sync_success_and_no_waiting_sync(self):
        if len(self.detected_files) == 0:
            self.status = "OK"
            Notification.get().update()

    def wait_connection(self):
        self.status = "Wait"
        Notification.get().update()

    def ready_connection(self):
        self.status = "Work"
