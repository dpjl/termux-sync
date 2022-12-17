import datetime

import termux

from sync.misc.Config import config
from sync.misc.Logger import logger


class Notification:
    __instance__ = None

    def __init__(self):
        self.sync_all = {}
        self.watchers = {}
        self.global_status = "Active"
        now_date = datetime.datetime.now()
        self.last_start = f"Started: {now_date.strftime('%Y-%m-%d@%H:%M:%S')}"
        self.last_stop = f"Stopped: -"
        self.last_start_stop_time = now_date.strftime('%a. %H:%M:%S')
        self.last_full_sync = f"Fully synchronized: -"

    @staticmethod
    def get() -> "Notification":
        if Notification.__instance__ is None:
            Notification.__instance__ = Notification()
        return Notification.__instance__

    def set_full_sync_status(self, sync_all):
        self.sync_all = sync_all
        self.update()

    def set_watchers(self, watchers):
        self.watchers = watchers
        self.update()

    def set_global_status(self, global_status):
        self.global_status = global_status

    def set_inactive(self):
        self.set_global_status("Inactive")
        now_date = datetime.datetime.now()
        self.last_stop = f"Stopped: {now_date.strftime('%Y-%m-%d@%H:%M:%S')}"
        self.last_start_stop_time = now_date.strftime('%a. %H:%M:%S')
        self.update()

    def set_active(self):
        self.set_global_status("Active")
        now_date = datetime.datetime.now()
        self.last_start = f"Started: {now_date.strftime('%Y-%m-%d@%H:%M:%S')}"
        self.last_start_stop_time = now_date.strftime('%a. %H:%M:%S')
        self.update()

    def full_sync_done(self):
        self.last_full_sync = f"Fully synchronized: {datetime.datetime.now().strftime('%Y-%m-%d@%H:%M:%S')}"
        self.update()

    def exiting(self):
        self.set_global_status("Exited")
        now_date = datetime.datetime.now()
        self.last_start_stop_time = now_date.strftime('%a. %H:%M:%S')
        self.update()

    def update(self):
        notification_title = f"Termux-sync [{self.global_status}] [{self.last_start_stop_time}]"
        notification_id = 999
        notification_content = ""

        if config.debug:
            notification_content += self.last_stop + "\n"
            notification_content += self.last_start + "\n"
            notification_content += self.last_full_sync + "\n"
            notification_content += "\n"

        for sync_info in config.sync_info_list:
            item_line = f"{sync_info.label} "
            if sync_info.id in self.sync_all:
                item_line += f"{self.sync_all[sync_info.id]} | "
            else:
                item_line += f"- | "
            if sync_info.id in self.watchers:
                watcher = self.watchers[sync_info.id]
                item_line += watcher.files_info.get_status()
                if watcher.last_sync_date is not None:
                    last_sync_date = watcher.last_sync_date.strftime('%H:%M:%S')
                    item_line += f" ({last_sync_date})"
            else:
                item_line += " [Not watching]"
            notification_content += item_line + "\n"
        action = f"termux-open --content-type yaml {logger.log_file}"

        termux.Notification.notify(notification_title,
                                   notification_content,
                                   notification_id,
                                   args=("alert-once", "ongoing"),
                                   kwargs={"button1": "See logs", "button1-action": action})
