from typing import Dict

from sync.misc.Config import ConfKey, config
from sync.misc.ConnectionStatusThread import ConnectionStatusThread
from sync.misc.Notification import Notification
from sync.watch.DirectoryWatcherThread import DirectoryWatcherThread
from sync.watch.INotifyThread import INotifyThread


class DirectoryWatcherList:

    def __init__(self, i_notify_thread: INotifyThread):
        self.watchers: Dict[str, DirectoryWatcherThread] = {}
        self.i_notify_thread = i_notify_thread
        self.connection_status = ConnectionStatusThread(config.get(ConfKey.test_url))
        for sync_info in config.sync_list():
            if sync_info.activated and sync_info.watch:
                watch_dir_thread = DirectoryWatcherThread(self.i_notify_thread, sync_info, self.connection_status)
                self.watchers[sync_info.id] = watch_dir_thread

    def start(self):
        self.connection_status.start()
        for watch_dir_thread in self.watchers.values():
            watch_dir_thread.start()
        Notification.get().set_watchers(self.watchers)

    def stop(self):
        for watch_dir_thread in self.watchers.values():
            watch_dir_thread.stop()
        self.connection_status.stop()
        Notification.get().set_watchers({})
