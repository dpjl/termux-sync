import os
from threading import Thread, Lock
from typing import List, Union

import select
from inotify_simple import INotify, masks

from sync.misc.Logger import logger


class INotifyThread(Thread):
    def __init__(self):
        self.i_notify = INotify()
        self.read_pipe_fd, write_pipe_fd = os.pipe()
        self.write_pipe_f = os.fdopen(write_pipe_fd, "wb")
        self.watch_list: "List[Union[DirectoryWatcherThread, CommandWatcher]]" = []
        self.lock = Lock()
        Thread.__init__(self)

    def add_i_notify_watch(self, path, _flags=masks.ALL_EVENTS):
        with self.lock:
            wd = self.i_notify.add_watch(path, _flags)
            logger.debug(f"INotify watch added: {wd} ({path})")
            return wd

    def remove_i_notify_watch(self, wd):
        with self.lock:
            self.i_notify.rm_watch(wd)
            logger.debug(f"INotify watch removed: {wd}")

    def register_watcher(self, watcher):
        self.watch_list.append(watcher)

    def unregister_watcher(self, watcher):
        self.watch_list.remove(watcher)

    def __wake_up_watcher(self, event):
        for watch in self.watch_list:
            if event.wd in watch:
                watch.wake_up(event)
                return

    def run(self):
        logger.print("THREAD: Start INotify thread")
        while True:
            rlist, _, _ = select.select([self.i_notify.fileno(), self.read_pipe_fd], [], [])

            if self.i_notify.fileno() in rlist:
                for event in self.i_notify.read(timeout=0):
                    self.__wake_up_watcher(event)

            if self.read_pipe_fd in rlist:
                os.close(self.read_pipe_fd)
                self.i_notify.close()
                logger.print("Stop INotify thread")
                return

    def stop(self):
        if not self.write_pipe_f.closed:
            self.write_pipe_f.write(b"\x00")
            self.write_pipe_f.close()
