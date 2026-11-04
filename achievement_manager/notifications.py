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

def _close_after_delay(notification_id):
    time.sleep(3)
    subprocess.run(["notify-send", "--close", notification_id])


def show_achievement(title, message):
    # Show a notification about achievement
    res = subprocess.run(
        ["notify-send", "-p", title, message, "-a", v.APP_NAME, "-i", v.APP_ICON],
        capture_output=True,
        text=True
    )
    # Get notification id
    notification_id = res.stdout.strip()
    # Start timer for closing notification in background
    if notification_id:
        threading.Thread(
            target=_close_after_delay,
            args=(notification_id,),
            daemon=True
        ).start()
