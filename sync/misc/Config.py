import json
import os
from enum import Enum
from pathlib import Path
from typing import List

from sync.misc.Logger import logger


class ConfKey(str, Enum):
    sync_delay = "sync-delay-in-seconds"
    debug = "debug"
    test_url = "test-url"
    start_time = "start-time"
    stop_time = "stop-time"
    sync_items = "sync-items"


class ConfSyncKey(str, Enum):
    type = "type"
    local_path = "local-path"
    remote_path = "remote-path"
    ignore_patterns = "ignore-patterns"
    label = "label"
    watch_depth = "watch-depth"
    watch_sync_mode = "watch-sync-mode"
    watch_new_dir = "watch-new-dir"
    root = "root"
    remote_root = "remote-root"
    watch = "watch"
    full_sync = "full-sync"
    ssh_port = "ssh-port"


STATUS_LABELS = {
    "Started": "⏳",
    "Wait": "⏳",
    "Work": "📤",
    "OK": "✔️"
}


class SyncInfo:

    def __init__(self, sync_id, info_dict):
        self.id = sync_id
        self.info_dict = info_dict

        self.type = self.get(ConfSyncKey.type, default="rsync")
        self.local_path = Path(self.get(ConfSyncKey.local_path))
        self.remote_path = self.get(ConfSyncKey.remote_path)
        self.ignore_patterns = self.get(ConfSyncKey.ignore_patterns, default=[])
        self.label = self.get(ConfSyncKey.label, default="")
        self.watch = self.get(ConfSyncKey.watch, default=False)
        self.watch_depth = self.get(ConfSyncKey.watch_depth, default=0)
        self.watch_sync_mode = self.get(ConfSyncKey.watch_sync_mode, default="all")
        self.watch_new_dir = self.get(ConfSyncKey.watch_new_dir, default=False)
        self.full_sync = self.get(ConfSyncKey.full_sync, default=False)
        self.root = self.get(ConfSyncKey.root, default=False)
        self.remote_root = self.get(ConfSyncKey.remote_root, default=False)
        self.ssh_port = self.get(ConfSyncKey.ssh_port, default=22)

        self.activated = True
        if not self.root and not os.path.exists(self.local_path):
            logger.print(f"Warning: {self.local_path} does not exist. This synchronization item will be ignored.")
            self.activated = False

    def get(self, key: ConfSyncKey, default=None):
        if key in self.info_dict:
            return self.info_dict[key]
        return default


class Config:

    def __init__(self):
        self.config_data = None
        self.sync_info_list: List[SyncInfo] = []
        self.commands_dir = None
        self.logs_file = None
        self.workspace_path = None
        self.debug = False

    def load(self, workspace_path, debug=False):
        self.workspace_path = workspace_path
        self.debug = debug
        config_path = Path(workspace_path) / "termux-sync.json"
        if os.path.exists(config_path):
            logger.print(f"Configuration file: {config_path}")
            with open(config_path) as config_file:
                self.config_data = json.load(config_file)
            for sync_id, sync in self.get(ConfKey.sync_items).items():
                self.sync_info_list.append(SyncInfo(sync_id, sync))
            self.commands_dir = Path(workspace_path) / "commands"
            self.logs_file = Path(workspace_path) / "termux-sync.log"
            return True
        else:
            logger.print(f"Configuration file {config_path} cannot be found in workspace.")
            return False

    def get(self, key: ConfKey):
        return self.config_data[key]

    def sync_list(self) -> List[SyncInfo]:
        return self.sync_info_list


config = Config()
