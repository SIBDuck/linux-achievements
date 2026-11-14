#!/usr/bin/env python3

# Copyright (C) 2026 SIBDuck
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Daemon that listens the terminal

import os
import atexit
import pathlib
from config import variables as v
v.DAEMON_PID_PATH.parent.mkdir(parents=True, exist_ok=True)
v.DAEMON_PID_PATH.write_text(str(os.getpid()), encoding="utf-8")

def remove_pid():
    v.DAEMON_PID_PATH.write_text("", encoding="utf-8")
atexit.register(remove_pid)


import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import cmd_parser
from achievement_manager import manager as mgr

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        abs_src = os.path.abspath(event.src_path)
        if abs_src == os.path.abspath(v.PATH_LCMD):
            try:
                with open(v.PATH_LCMD, "r", encoding="utf-8") as f:
                    new_cmd = f.read().strip()
                if new_cmd:
                    v.cmd = new_cmd
                    code = cmd_parser.parser.parse_list()
                    if code:
                        v.min_len = 4 if len(v.parsed) > 1 and v.parsed[1] == "END" else 3
                        if len(v.parsed) >= v.min_len:
                            current_trigger = (v.parsed[0], v.parsed[1])
                            if not hasattr(v, "last_trigger") or v.last_trigger != current_trigger:
                                v.last_trigger = current_trigger
                                mgr.achievement_manager.update(v.parsed)


            except FileNotFoundError:
                pass
        elif abs_src == os.path.abspath(v.PATH_EDITOR):
            try:
                with open(v.PATH_EDITOR, "r", encoding="utf-8", errors="ignore") as f:
                    new_editor = f.read().strip()
                if new_editor and new_editor != v.editor:
                    v.editor = new_editor
            except FileNotFoundError:
                pass

def main():
    path_obj = pathlib.Path(v.PATH_LCMD)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.touch(exist_ok=True)

    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path = str(path_obj.parent), recursive = False)
    observer.daemon = True
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()
