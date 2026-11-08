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




import time
import threading
import subprocess
import pathlib
import sys
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
from config import variables as v

def show_achievement(title, message):
    cmd = [
        "gdbus", "call", "--session",
        "--dest", "org.freedesktop.Notifications",
        "--object-path", "/org/freedesktop/Notifications",
        "--method", "org.freedesktop.Notifications.Notify",
        v.APP_NAME, # App name
        "0", # Replacement ID (0 - create new)
        str(v.APP_ICON.resolve()),  # Icon path (string only)
        title, # Header
        message, # Body (description)
        "[]", # Buttons (close button by default)
        "{'urgency': <byte 2>}", # Importance level (2 - critical. Notification would be on top of some windows)
        str(3000) # Timeout (milliseconds)
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)