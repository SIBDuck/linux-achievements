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



import os
import json
from config import variables as v
def os_join(path):
    return os.path.expanduser(path)

def add_to_path(shell):
    print(f"Installing config for {shell}...")
    if shell == "bash":
        logger_out = f"$HOME/.local/bin/cmd_tm_{shell}.sh"
    elif shell == "zsh":
        logger_out = f"$HOME/.local/bin/cmd_tm_{shell}.zsh"
    else:
        logger_out = f"$HOME/.local/bin/cmd_tm.fish"
    try:
        match shell:
            case "bash" | "zsh":

                target_file = os_join(f"~/.{shell}rc")
                """line_to_add = ('# ===SCRIPT FOR LOGGING TERMINAL (LINUX ACHIEVEMENTS)===',
                               '\nexport PATH="$HOME/.local/bin:$PATH"\n',
                               '# ===SCRIPT FOR LOGGING TERMINAL (LINUX ACHIEVEMENTS) ===\n')"""
                line_to_add = (
                        "\n# === TERM LOGGER START ===\n"
                        'if [ -z "$UNDER_LOGGER" ] && [ -x "' + logger_out + '" ]; then\n'
                        '    export UNDER_LOGGER=1\n'
                        '    exec "' + logger_out + '"\n'
                        "fi\n"
                       "# === TERM LOGGER END ===\n"
                )

                if not os.path.exists(target_file):
                    with open(target_file, "w", encoding='utf-8'):
                        pass
                with open(target_file, "r", encoding='utf-8') as f:
                    content = f.read()

                if "TERM LOGGER START" not in content:
                    with open(target_file, "a", encoding='utf-8') as f:
                        if content and not content.endswith("\n"):
                            f.write("\n")
                        f.write(line_to_add)
            case "fish":

                """config_dir = os.path.expanduser("~/.config/fish")
                target_file = os.path.join(config_dir, "config.fish")
                line_to_add = "fish_add_path ~/.local/bin\n"
    
                os.makedirs(config_dir, exist_ok=True)"""
                config_dir = str(os_join("~/.config/fish"))
                target_file = os.path.join(config_dir, "config.fish")

                line_to_add = (
                    "# === TERM LOGGER START ===\n"
                    "if not set -q UNDER_LOGGER; and test -x ~/.local/bin/term-logger\n"
                    "    set -gx UNDER_LOGGER 1\n"
                    "    exec ~/.local/bin/term-logger\n"
                    "end\n"
                    "# === TERM LOGGER END ===\n"
                )
                os.makedirs(config_dir, exist_ok=True)
                if not os.path.exists(target_file):
                    with open(target_file, 'w', encoding='utf-8') as f:
                        pass

                with open(target_file, "r", encoding='utf-8') as f:
                    content = f.read()

                if "TERM LOGGER START" not in content:
                    with open(target_file, 'a', encoding='utf-8') as f:
                        if content and not content.endswith("\n"):
                            f.write("\n")
                        f.write(line_to_add)
        DATA_PATH = v.DATA_PATH

        with open(DATA_PATH, "r", encoding='utf-8') as f:
            data = json.load(f)
        if not data["configs_installed"][shell]:
            data["configs_installed"][shell] = True
        with open(DATA_PATH, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Successfully installed the config for your shell: {shell}")

    except Exception as e:
        print(f"Something went wrong, installing config for {shell}. Error code: {e}")
