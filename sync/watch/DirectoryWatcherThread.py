import datetime
import os
from pathlib import Path
from threading import Thread, Event
from typing import Dict

from inotify_simple import flags, Event as INotifyEvent

from sync.misc.Config import ConfKey, config, SyncInfo
from sync.misc.FilesInformation import FilesInformation
from sync.misc.Logger import logger
from sync.watch.INotifyThread import INotifyThread
from sync.wrapper.RClone import RClone
from sync.wrapper.RSync import RSync


class DirectoryWatcherThread(Thread):

    def __init__(self, i_notify_thread: INotifyThread, sync_info: SyncInfo, connection_status):

        Thread.__init__(self)

        self.sync_info = sync_info

        self.files_info = FilesInformation(self.sync_info.id)
        if self.sync_info.type == "rclone":
            self.sync_tool = RClone(self.sync_info.local_path, self.sync_info.remote_path)
        elif self.sync_info.type == "rsync":
            self.sync_tool = RSync(self.sync_info.local_path, self.sync_info.remote_path)

        self.connection_status = connection_status
        self.stop_required = False
        self.last_start_date = None
        self.last_sync_date = None
        self.something_happened = Event()
        self.i_notify_thread = i_notify_thread
        self.wd_map: Dict[int, Path] = {}
        self.__init_i_notify_watches(Path(self.sync_info.local_path))
        logger.print(f"Number of i_notify watches created for {self.sync_info.id}: {len(self.wd_map.keys())}")
        self.i_notify_thread.register_watcher(self)

    def __contains__(self, wd):
        return wd in self.wd_map

    def is_path(self, path):
        return Path(path) == self.sync_info.local_path

    def __init_i_notify_watches(self, path):
        # put also flags.MOVED_TO ?
        wd = self.i_notify_thread.add_i_notify_watch(path, _flags=(flags.MODIFY | flags.CREATE))
        self.wd_map[wd] = path

        if self.sync_info.max_depth == -1 or (self.__depth(wd) + 1 <= self.sync_info.max_depth):
            for f in os.scandir(path):
                if f.is_dir():
                    if not self.__ignore(f.name):
                        self.__init_i_notify_watches(path / f.name)

    def __remove_i_notify_watcher(self):
        for wd in self.wd_map.keys():
            self.i_notify_thread.remove_i_notify_watch(wd)

    def __new_sub_dir_detected(self, event):
        if self.sync_info.watch_new_dir and (
                self.sync_info.max_depth == -1 or (self.__depth(event.wd) + 1 <= self.sync_info.max_depth)):
            new_path = self.wd_map[event.wd] / event.name
            wd = self.i_notify_thread.add_i_notify_watch(new_path)
            self.wd_map[wd] = new_path

    def __depth(self, wd):
        return len(self.wd_map[wd].relative_to(self.sync_info.local_path).parents)

    def __ignore(self, object_name):
        if self.sync_info.ignore_patterns is not None:
            for pattern in self.sync_info.ignore_patterns:
                if pattern in object_name:
                    return True
        return False

    # Wake up the thread
    def wake_up(self, event: INotifyEvent):
        event_flags = flags.from_mask(event.mask)
        if config.get(ConfKey.debug):
            print(f"{event} {[f.name for f in event_flags]}")
        if not self.__ignore(event.name):
            if flags.CREATE in event_flags and flags.ISDIR in event_flags:
                self.__new_sub_dir_detected(event)
            elif flags.ISDIR not in event_flags and event.name != "":
                self.something_happened.set()
                self.files_info.detected_file(event.name)

    # Stop the thread
    def stop(self):
        self.i_notify_thread.unregister_watcher(self)
        self.__remove_i_notify_watcher()
        self.stop_required = True
        self.something_happened.set()
        self.files_info.close()

    # Threaded method
    def run(self):
        logger.print("THREAD: Start thread in charge of synchronizing " + self.sync_info.local_path)
        self.something_happened.wait()
        self.something_happened.clear()

        while True:
            if self.stop_required:
                logger.print("Stop thread in charge of synchronizing " + self.sync_info.local_path)
                return
            if self.last_start_date is None:
                self.last_start_date = datetime.datetime.now()
            sync_delay = config.get(ConfKey.sync_delay)
            logger.print(f"Thread has been alerted of at least one change. "
                         f"Wait {sync_delay} seconds and update.")
            if not self.something_happened.wait(sync_delay):
                if self.__execute_sync_tool():
                    self.something_happened.wait()
                else:
                    logger.print(
                        f"{self.sync_info.type} call failed. Wait another iteration before retrying to call it.")
                    continue
            self.something_happened.clear()

    def __execute_sync_tool(self):

        sync_success = False
        last_start_date = self.last_start_date

        self.connection_status.update()
        if not self.connection_status.is_connection_ok():
            self.files_info.wait_connection()
        self.connection_status.ok.wait()
        self.files_info.ready_connection()

        if self.last_start_date is not None:
            duration = int((datetime.datetime.now() - self.last_start_date).total_seconds()) + 60
            self.last_start_date = None
        else:
            # there should be nothing to send because last_start_date is reinitialized just BEFORE rcloning
            # so it means: nothing has been detected since last rclone execution
            return

        for file_path in self.sync_tool.run(duration=duration):
            self.files_info.synchronized_file(Path(file_path).name)

        if self.sync_tool.return_code != 0:
            self.last_start_date = last_start_date
        else:
            sync_success = True
            self.last_sync_date = datetime.datetime.now()
            if self.last_start_date is None:
                self.files_info.sync_success_and_no_waiting_sync()
        return sync_success
