import time
from threading import Thread

from cron_descriptor import ExpressionDescriptor
from crontab import CronTab

from sync.misc.Logger import logger


class ActionSchedulerThread(Thread):
    def __init__(self, action, cron_expression):
        Thread.__init__(self)
        self.action = action
        self.cron_tab = CronTab(cron_expression)
        logger.print(f"Start schedule thread of action: {action}")
        logger.print(f"Schedule cron expression: {cron_expression}")
        logger.print(f"This cron expression means: {str(ExpressionDescriptor(cron_expression))}")

    def run(self):
        while True:
            logger.print(f"THREAD: start thread to schedule action {self.action}")
            seconds_to_wait = self.cron_tab.next(default_utc=False)
            logger.print(f"Wait for {seconds_to_wait} seconds before executing {self.action}")
            time.sleep(seconds_to_wait)
            self.action()
