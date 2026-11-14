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

import pathlib
import sys
import shlex
#ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
ROOT_DIR = pathlib.Path.home()
ROOT_DIR = ROOT_DIR / "Linux Achievements" / "config"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from . import storage
from . import notifications
from config import variables as v

import re
import os


class Achievement:
    def __init__(self):
        self.db = storage.JsonStorage()
        self.achs = self.db.load_achs()
        self.player_data = self.db.load_data()
        self.cheated = self.db.cheated

    def update(self, pcmd: list):
        self.player_data = self.db.load_data()
        self.cheated = self.db.cheated

        # =========

        self.cheater()
        self.vim_detector(pcmd)
        self.vi_detector(pcmd)
        self.player_data = self.db.load_data()
        self.vim_time()
        self.default_achievements(pcmd)
        self.player_data = self.db.load_data()
        self.repeater(pcmd)
        self.vim_nano_exist(pcmd)
        self.player_data = self.db.load_data()
        """
        self.poweroff_reboot(pcmd)
        self.ls_a(pcmd)
        self.shrc(pcmd)
        self.rm_rf_as(pcmd)
        self.vim_close(pcmd)
        self.nano_close(pcmd)
        self.nano_open(pcmd)
        """


        # =========

    def vim_timecount(self, pcmd: list):
        """ pcmd = [time (seconds),  status ("START"|"END"), exit_code (not necessary, if status == "START"), command, attributes]
        e.g.: ["1794643103", "END", "0", "la", "daemon", "--stop"]
        e.g.: ["1794644348", "START", "nvim", "~/.bashrc"]
        """
        status = pcmd[1]
        current_time = int(pcmd[0])
        if status == "START":
            v.vim_tm1 = current_time
            return

        if status == "END":
            v.vim_tm2 = current_time
            duration_s = v.vim_tm2 - v.vim_tm1
            session_minutes = duration_s / 60

            data = self.db.load_data()
            data["stats"]["time"]["vim"] += session_minutes
            self.db.save_data(data)

    def vim_time_conv(self, total_minutes: float):
        # Converts time spent in vim from seconds into hours and minutes respectively
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return [hours, minutes]
    def vim_detector(self, pcmd: list):
        cmd = shlex.join(pcmd[3:]) if pcmd[1] == "END" else shlex.join(pcmd[2:])
        if re.search(v.vim_find_re, cmd, re.IGNORECASE):
            self.vim_timecount(pcmd)


    def cheater(self):
        ach = self.player_data["achievements"]["sh.cheater"]
        if self.cheated and not ach["done"]:
            self.show_ach("sh.cheater")

    def find_re(self, pcmd: list, RE, ach_mt, return_re_search=False):
        cmd = shlex.join(pcmd[3:]) if pcmd[1] == "END" else shlex.join(pcmd[2:])
        match = re.search(RE, cmd, re.IGNORECASE)
        res = match if not ach_mt["done"] else None

        return res, match if return_re_search else res

    def vi_detector(self, pcmd: list):
        ach = "vim.open.vi"
        self.player_data = self.db.load_data()
        ach_meta = self.player_data["achievements"][ach]
        if self.find_re(pcmd, v.vi_find_re, ach_meta):
            self.show_ach(ach)

    def show_ach(self, ach, update_db=True):
        ach_txt = self.achs[ach]
        ach_data = self.player_data["achievements"][ach]
        ach_data["done"] = True
        title = ach_txt["title"]
        description = ach_txt["description"]
        notifications.show_achievement(title, description)
        if update_db:
            self.db.save_data(self.player_data)


    def vim_time(self):
        minutes = self.player_data["stats"]["time"]["vim"]
        hours = minutes // 60

        # Mapping layout updated to check the correct index types:
        # (time_value, variable_to_check, achievement_id)
        stockholm_thresholds = [
            (10, minutes, "vim.time.stockholm.1"),  # 10 minutes
            (30, minutes, "vim.time.stockholm.2"),  # 30 minutes
            (1, hours, "vim.time.stockholm.3"),  # 1 hour
            (5, hours, "vim.time.stockholm.4"),  # 5 hours
            (10, hours, "vim.time.stockholm.5"),  # 10 hours
            (24, hours, "vim.time.stockholm.6"),  # 24 hours
            (50, hours, "vim.time.stockholm.7"),  # 50 hours
            (100, hours, "vim.time.stockholm.8"),  # 100 hours
            (500, hours, "vim.time.stockholm.9"),  # 500 hours
            (1000, hours, "vim.time.stockholm.10"),  # 1000 hours
        ]
        data_changed = False
        for threshold, current_value, ach_id in stockholm_thresholds:
            achievement = self.player_data["achievements"][ach_id]
            if current_value >= threshold and not achievement["done"]:
                data_changed = True
                self.show_ach(ach_id, update_db=False)

        if data_changed:
            self.db.save_data(self.player_data)

    def recursion(self, cmd: str):
        cmd = shlex.join(cmd)
        ach = "sh.recursion.la"
        ach_meta = self.player_data["achievements"][ach]
        match = re.search(v.RECURSION_PATTERN, cmd)
        if match and not ach_meta["done"]:
            ach_meta["done"] = True
            self.show_ach(ach)


    def default_achievements(self, pcmd: list):
        thresholds = [
            # Achievement id, regex, execution status ("START"|"END"|"", "" - does not matter),
            ("sh.poweroff", v.poweroff_find_re, "END", "1"), # expected exit code (e.g.: "1" (E.C. 1 is expected, "!0" - not 0 is expected, "" - does not matter)
            ("sh.reboot", v.reboot_find_re, "END", "1"),
            ("sh.xray", v.ls_a_find_re, "END", "0"),
            ("sh.shrc", v.shrc_find_re, "END", "0"),
            ("sh.kill_try", v.rm_rf_find_re, "END" ,"!0"),
            ("nano.open", v.nano_find_re, "END", ""),
            ("vim.close.200", v.vim_find_re, "END", "0"),
            ("vim.close.force", v.vim_find_re, "END", "!0"),
            ("nano.close.200", v.nano_find_re, "END", "0"),
            ("nano.close.force", v.nano_find_re, "END", "!0"),


        ]
        data_changed = False
        actual_ec = pcmd[2]
        actual_sts = pcmd[1]

        for ach, regex, sts, ec in thresholds:
            ach_meta = self.player_data["achievements"][ach]
            if ec.startswith("!"):
                if self.find_re(pcmd, regex, ach_meta) and actual_ec != ec[1:] and actual_sts == sts:
                    self.show_ach(ach, update_db=False)
                    data_changed = True
                continue

            if self.find_re(pcmd, regex, ach_meta) and actual_ec == ec and actual_sts == sts:
                self.show_ach(ach, update_db=False)
                data_changed = True

        if data_changed:
            self.db.save_data(self.player_data)

    def repeater(self, pcmd):
        ach = "sh.repeater"
        ach_meta = self.player_data["achievements"][ach]

        if self.find_re(pcmd, v.last_cmd_find_re, ach_meta):
            if not hasattr(v, "repeater_times"):
                v.repeater_times = 0
            if not hasattr(v, "t1"):
                v.t1 = int(pcmd[0])
                v.repeater_times = 1
                return
            current_time = int(pcmd[0])
            last_time = int(v.t1)

            if current_time - last_time < 60:
                v.repeater_times += 1
                v.t1 = current_time
            else:
                v.repeater_times = 0
                if hasattr(v, "t1"):
                    del v.t1
                return
            if v.repeater_times == 3:
                self.show_ach(ach)
                v.repeater_times = 0
                if hasattr(v, "t1"):
                    del v.t1

    def vim_nano_exist(self, pcmd):
        ach = "vim_nano.new_exisitng_file"
        ach_meta = self.player_data["achievements"][ach]
        findre, match = self.find_re(pcmd, v.vim_nano_exst_find_re, ach_meta, return_re_search=True)
        if match is not None:
            path = next(item for item in match.groups() if item is not None).strip().replace('\\ ', ' ')
            full_path = os.path.expanduser(path)
            if not os.path.exists(full_path):
                self.show_ach(ach)
    def cli_achs(self, cmd: str):
        self.recursion(cmd)

achievement_manager = Achievement()