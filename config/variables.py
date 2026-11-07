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

"""The module that contains variables"""

import os
import pathlib

# Names
DAEMON_NAME = "lad"
UTILITY_NAME = "la"
APP_NAME = "Linux Achievements"
running = True
CURRENT_SHELL = None
record = True
# Paths
# Shells
BASH_BINARY_PATH = pathlib.Path("/usr/bin/bash")
ZSH_BINARY_PATH = pathlib.Path("/usr/bin/zsh")
FISH_BINARY_PATH = pathlib.Path("/usr/bin/fish")
HOME_DIR = pathlib.Path.home()
XDG_PATH = pathlib.Path(os.getenv("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}") + "/linux-achievements")
GOTO_DIR = None # pathlib.Path()
PATH_LCMD = XDG_PATH / "last_cmd"
PATH_EDITOR = XDG_PATH / "editor"
PATH_DISABLED = XDG_PATH / "disabled"
PROJECT_DIR = HOME_DIR / "Linux Achievements"
APP_ICON = PROJECT_DIR / "images" / "tux.png"
LOG_FILE_PATH = HOME_DIR / 'Linux Achievements' / "tmp" / 'daemon.log'
DATA_PATH = PROJECT_DIR / "data" / "player_data.json"
ACHIEVEMENT_PATH = PROJECT_DIR / "data" / "achievements.json"

DAEMON_BIN_PATH = HOME_DIR / ".local" / "bin" / DAEMON_NAME
DAEMON_PID_PATH = HOME_DIR / "Linux Achievements" / "tmp" / "daemon.pid"

cmd = ''
parsed = ''
# State variables
vim_time_s = 0
vim_time_ = 0
vim_tm1 = 0
vim_tm2 = 0
editor = None
last_trigger = None
vim_time_flag = False
vim_close_flag = False
open_vi_flag = False
rm_rf_flag = False
poweroff_reboot_flag = False
ls_a_flag = False
shrc_flag = False
repeater_flag = False
nano_close_flag = False
nano_open_flag = False
vim_nano_exst_flag = False
t1 = 0
repeater_times = 0
# Patterns
BASH_PATTERN = r"^:\s*(.*?)\s*$"
ACH_ID_PATTERN = r"^\s*ach\s+((?:['\"]?[a-zA-Z0-9_.-]+['\"]?\s*)+)$"
SHELL_SELECT_PATTERN = r"^\s*shell\s+([\w-]+)\s*$"
PIPE_PATTERN = r"^(?!:!)([^|]+)\|(.*)"
vim_find_re = r"^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*(vim|vi|micro|nvim|view|vimdiff)(?:\s+|$)"
vi_find_re = r"^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*(vi)(?:\s+|$)"
ls_a_find_re = r"^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*ls\s+-(?:[^\s]*a[^\s]*)(?:\s+|$)"
poweroff_find_re = r"^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*poweroff\s*$"
reboot_find_re = r"^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*reboot\s*$"
shrc_find_re = r"^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*(?:vi|vim|nvim|micro|emacs|nano)\s+(?:~?\/)?\.[^\s]*shrc\s*$"
rm_rf_find_re = r"^\s*rm\s+-(?:[^\s]*r[^\s]*f|[^\s]*f[^\s]*r|[^\s]*r\s+-[^\s]*f|[^\s]*f\s+-[^\s]*r)\s+\/\s*$"
nano_find_re = r"^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*(nano)(?:\s+|$)"
vim_nano_exst_find_re = r"""^\s*(?:(?:sudo|su|env|time|nice|setsid|nohup|stdbuf)\s+(?:-[^\s]+\s+)*)*(?:vi|vim|nvim|micro|emacs|nano)\s+(?:-[^\s]+\s+)*(?:"([^"\\n]+)"|'([^'\\n]+)'|((?:[^\s\\n]|\\ )+))\s*$"""
last_cmd_find_re = r"^\s*!!\s*$"
