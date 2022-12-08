import argparse
import os
import signal
import time
from threading import Lock, active_count

from sync.misc.ActionSchedulerThread import ActionSchedulerThread
from sync.misc.Config import ConfKey, config
from sync.misc.Logger import logger
from sync.misc.Notification import Notification
from sync.watch.CommandWatcher import CommandWatcher
from sync.watch.DirectoryWatcherList import DirectoryWatcherList
from sync.watch.INotifyThread import INotifyThread
from sync.wrapper.RClone import RClone
from sync.wrapper.RSync import RSync

signal.signal(signal.SIGINT, signal.SIG_DFL)


class Main:
    def __init__(self, __workspace_path):
        self.workspace_path = __workspace_path
        ActionSchedulerThread(self.start, config.get(ConfKey.start_time)).start()
        ActionSchedulerThread(self.stop, config.get(ConfKey.stop_time)).start()
        self.i_notify_thread = INotifyThread()
        self.command_watcher = CommandWatcher(self.i_notify_thread)
        self.watch_list = None
        self.started = False
        self.lock = Lock()

    def run(self):
        self.i_notify_thread.start()
        try:
            self.start()
            self.stop()
            for command in self.command_watcher.watch():
                if command == "start":
                    self.start()
                elif command == "stop":
                    self.stop()
        finally:
            self.i_notify_thread.stop()

    @staticmethod
    def set_airplane_state(state):
        cmd1 = f"settings put global airplane_mode_on {state}"
        cmd2 = "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true"
        os.system(f'su -c "{cmd1} && {cmd2}"')

    def pre_start(self):
        pass

    def start(self):
        with self.lock:
            if not self.started:
                logger.print("Starting termux-sync watchers")
                self.full_sync()
                self.watch_list = DirectoryWatcherList(self.i_notify_thread)
                self.watch_list.start()
                self.started = True
                logger.print(f"Number of active thread(s): {active_count()}")

    def stop(self):
        with self.lock:
            if self.started:
                logger.print("Stopping termux-sync watchers")
                self.watch_list.stop()
                self.watch_list = None
                self.started = False
                time.sleep(5)
                logger.print(f"Number of active thread(s): {active_count()}")

    @staticmethod
    def full_sync():
        logger.print(">>> Full sync start")
        full_sync_status = {}
        for sync_info in config.sync_list():

            if config.get(ConfKey.debug):
                logger.print(f"Check if {sync_info.id} has to be synchronized")

            if sync_info.activated and sync_info.full_sync:
                sync_tool = None
                if sync_info.type == "rclone":
                    sync_tool = RClone(sync_info.local_path, sync_info.remote_path)
                elif sync_info.type == "rsync":
                    sync_tool = RSync(sync_info.local_path, sync_info.remote_path)

                if sync_tool:
                    logger.print(f"Full sync of {sync_info.id}")
                    nb_files_sync = 0
                    for file_path in sync_tool.run(root=sync_info.root):
                        nb_files_sync += 1
                        if config.get(ConfKey.debug):
                            logger.print(f"Synchronized file: {file_path}")
                    logger.print(f"Full sync: {nb_files_sync} files synchronized")
                    full_sync_status[sync_info.id] = nb_files_sync
        Notification.get().set_full_sync_status(full_sync_status)
        logger.print("<<< Full sync end")


def parse_args():
    parser = argparse.ArgumentParser(
        prog='termux-sync',
        description='Command line tools for files synchronization between mobile and cloud. '
                    'Synchronization itself is done using rclone or rsync. '
                    'Optional file watching is done using inotify. ')

    parser.add_argument('-w', '--workspace', default="./.termux-sync", help='Specify a workspace folder')
    parser.add_argument('-s', '--stdout', action='store_true', help='Display logs on stdout')
    parser.add_argument('-d', '--debug', action='store_true', help='Display debug logs')
    return parser.parse_args()


# TODO Les compteurs sont historisés et remis à 0.
if __name__ == "__main__":
    args = parse_args()
    if not os.path.exists(args.workspace):
        print(f"Workspace '{args.workspace}' does not exist.")
        exit(0)
    logger.load(args.workspace, args.stdout, args.debug)
    config.load(args.workspace)
    Main(args.workspace).run()
