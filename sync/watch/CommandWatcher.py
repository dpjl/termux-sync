import os
from pathlib import Path
from threading import Event

from inotify_simple import flags, Event as INotifyEvent

from sync.misc.Config import ConfKey, config
from sync.misc.Logger import logger
from sync.watch.INotifyThread import INotifyThread


class CommandWatcher:
    last_command = None

    def __init__(self, i_notify_thread: INotifyThread):

        self.i_notify_thread = i_notify_thread
        self.command_received = Event()
        self.commands_dir = config.commands_dir
        self.wd = None

        if not os.path.exists(self.commands_dir):
            logger.print(f"Folder {self.commands_dir} does not exist, commands will not be watched")
            return

        logger.print(f"Start watching command files in  {self.commands_dir}")

        for file_name in os.listdir(Path(self.commands_dir)):
            os.remove(Path(self.commands_dir) / file_name)

        self.wd = self.i_notify_thread.add_i_notify_watch(self.commands_dir, _flags=flags.CREATE)
        self.i_notify_thread.register_watcher(self)

    def __contains__(self, wd):
        return wd == self.wd

    def is_path(self, path):
        return Path(path) == self.commands_dir

    def remove(self):
        pass

    def process_new_dir(self, event):
        pass

    def wake_up(self, event: INotifyEvent):
        event_flags = flags.from_mask(event.mask)
        if config.get(ConfKey.debug):
            print(f"{event} {[f.name for f in event_flags]}")
        CommandWatcher.last_command = event.name
        self.command_received.set()

    def watch(self):
        while True:
            self.command_received.wait()
            self.command_received.clear()
            yield CommandWatcher.last_command
            command_file = Path(self.commands_dir) / self.last_command
            if os.path.exists(command_file):
                os.remove(command_file)
