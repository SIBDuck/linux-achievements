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
ROOT_DIR = pathlib.Path.home()
ROOT_DIR = ROOT_DIR / "Linux Achievements" / "config"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from . import crypto
from config import variables as v
import json



class JsonStorage:
    def __init__(self):
        self.cheated = False
        self.ACHIEVEMENT_PATH = v.ACHIEVEMENT_PATH
        self.DATA_PATH = v.DATA_PATH
    def load_achs(self):
        with open(self.ACHIEVEMENT_PATH, "r", encoding='utf-8') as f:
            return json.load(f)
    def load_data(self):
        with open(self.DATA_PATH, "r", encoding='utf-8') as f:
            raw_data = json.load(f)

        saved_shash = raw_data.pop("file_hash", None)
        calced_hash = crypto.calculate_hash(raw_data)
        if saved_shash != calced_hash:
            self.cheated = True

        return raw_data


    def save_data(self, data_dict):
        data_dict.pop("file_hash", None)
        current_hash = crypto.calculate_hash(data_dict)
        data_dict["file_hash"] = current_hash

        with open(self.DATA_PATH, "w", encoding='utf-8') as f:
            json.dump(data_dict, f, indent=4, ensure_ascii=False)



