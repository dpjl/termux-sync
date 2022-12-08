import urllib.request
from threading import Event, Thread

from sync.misc.Logger import logger


class ConnectionStatusThread(Thread):
    def __init__(self, url_to_test):
        self.url_to_test = url_to_test
        Thread.__init__(self)

        self.connection_ok = False
        self.ok = Event()
        self.ko = Event()
        self.ok.clear()
        self.ko.set()

        self.stop_required = False

    def update(self):
        try:
            urllib.request.urlopen(self.url_to_test, timeout=60)
            self.connection_ok = True
            self.ok.set()
            self.ko.clear()
        except:
            self.connection_ok = False
            self.ko.set()
            self.ok.clear()

    def is_connection_ok(self):
        return self.connection_ok

    def run(self):
        logger.print("THREAD: start to monitor connection status")
        while True:
            if self.stop_required:
                logger.print("Stop monitoring connection status")
                return
            self.ko.wait()
            while not self.connection_ok:
                try:
                    urllib.request.urlopen(self.url_to_test, timeout=10)
                except:
                    self.ok.wait(10 * 60)
                    continue
                self.connection_ok = True
                self.ko.clear()
                self.ok.set()

    def stop(self):
        self.stop_required = True
        self.ko.set()
        self.ok.set()
