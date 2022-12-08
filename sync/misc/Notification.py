import termux

from sync.misc.Config import ConfKey, config
from sync.misc.Logger import logger


class Notification:
    __instance__ = None

    def __init__(self):
        self.sync_all = {}
        self.watchers = {}
        self.global_status = "Active"

    @staticmethod
    def get():
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

    def update(self):
        notification_title = f"Sync with cloud ({self.global_status})"
        notification_id = 999
        notification_content = ""

        for item_id in config.get(ConfKey.sync_items).keys():
            item_line = ""
            if item_id in self.sync_all:
                item_line += f"[{self.sync_all[item_id]}] "
            if item_id in self.watchers:
                item_line += self.watchers[item_id].files_info.get_status()
            notification_content += item_line + "\n"
        action = f"termux-open {logger.log_file}"

        #termux.Notification.notify(notification_title,
        #                           notification_content,
        #                           notification_id,
        #                           args=("alert-once", "ongoing"),
        #                           kwargs={"button1": "See logs", "button1-action": action})
