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



import json
import pathlib
import re
import shlex
import sys
import variables as v

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

class Parser:
    def __init__(self):
        pass
    def parse_list(self):
        v.parsed = re.sub(r'\b--color=auto\b', "", v.cmd)
        # Parses to [time (seconds from 01.01.1970), command (may consist of a few elements (el1, el2...), success code (int))]
        try:
            v.parsed = shlex.split(v.parsed, comments=True)

            return True
        except ValueError:
            return False
    def resolve_alias(self, log):
        cmd = v.parsed[2:-1]
        cmd_resolved = None


parser = Parser()