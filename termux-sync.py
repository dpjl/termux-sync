import argparse
import os
import signal
import time
from pathlib import Path
from threading import Lock, active_count

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
        self.i_notify_thread = INotifyThread()
        self.command_watcher = CommandWatcher(self.i_notify_thread)
        self.watch_list = None
        self.started = False
        self.lock = Lock()

    def run(self, full_sync, monitor, command):
        if command is not None:
            self.send_command(command)
            exit(0)
        if full_sync:
            self.full_sync()
        if monitor:
            Notification.get().update()
            self.i_notify_thread.start()
            try:
                self.start()
                for command in self.command_watcher.watch():
                    logger.print(f"'{command}' command received.")
                    if command == "start":
                        self.start()
                    elif command == "stop":
                        self.stop()
                    elif command == "sync":
                        self.full_sync()
                    elif command == "exit":
                        Notification.get().exiting()
                        logger.print("Exit application now.")
                        exit(0)
            finally:
                self.i_notify_thread.stop()

    @staticmethod
    def send_command(command):
        if os.path.exists(config.commands_dir):
            logger.print(f"Send command {command}")
            command_file = Path(config.commands_dir) / command
            if os.path.exists(command_file):
                os.remove(command_file)
            command_file.touch()

    def start(self):
        with self.lock:
            if not self.started:
                logger.print("Starting termux-sync watchers")
                Notification.get().set_active()
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
                Notification.get().set_inactive()
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
                    sync_tool = RSync(sync_info.local_path, sync_info.remote_path, sync_info.ssh_port)

                if sync_tool:
                    logger.print(f"Full sync of {sync_info.id}")
                    nb_files_sync = 0
                    for file_path in sync_tool.run(root=sync_info.root, remote_root=sync_info.remote_root):
                        nb_files_sync += 1
                        if config.get(ConfKey.debug):
                            logger.print(f"Synchronized file: {file_path}")
                    logger.print(f"Full sync: {nb_files_sync} files synchronized")
                    if sync_tool.return_code != 0:
                        full_sync_status[sync_info.id] = "ERROR"
                    else:
                        full_sync_status[sync_info.id] = nb_files_sync
                    Notification.get().set_full_sync_status(full_sync_status)
        Notification.get().full_sync_done()
        logger.print("<<< Full sync end")


def parse_args():
    pars = argparse.ArgumentParser(
        prog='termux-sync',
        description='Command line tools for files synchronization between mobile and cloud. '
                    'Synchronization itself is done using rclone or rsync. '
                    'Optional file watching is done using inotify. ')

    pars.add_argument('-w', '--workspace', default="./.termux-sync", help='Specify a workspace folder')
    pars.add_argument('-c', '--command', default=None, help='Send a specific command to a termux-sync already started')
    pars.add_argument('-f', '--full-sync', action='store_true', default=False, help='Full synchronization')
    pars.add_argument('-m', '--monitor', action='store_true', default=True, help='Monitor changes and synchronize them')
    pars.add_argument('-s', '--stdout', action='store_true', default=False, help='Display logs on stdout')
    pars.add_argument('-v', '--verbose', action='store_true', default=False, help='Display also debug logs')
    return pars.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.workspace):
        print(f"Workspace '{args.workspace}' does not exist.")
        exit(0)
    logger.load(args.workspace, args.stdout, args.verbose)
    config.load(args.workspace, args.verbose)
    Main(args.workspace).run(args.full_sync, args.monitor, args.command)


# TODO Les compteurs sont historisés et remis à 0.
if __name__ == "__main__":
    args = parse_args()
    if not os.path.exists(args.workspace):
        print(f"Workspace '{args.workspace}' does not exist.")
        exit(0)
    main()
