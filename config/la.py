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
# CLI utility to control the daemon and player's progress

import time
import subprocess
import pathlib
import os
import re
import sys
import io
import json
import install_conf
import variables as v
import psutil
import shlex


class Parser:
    def __init__(self):
        pass
    def parse(self, log, native_only=False, is_cli=True):
        try:
            parts = shlex.split(log)
            if not parts:
                return
        except ValueError as e:
            print(f"{e}")
            return

        cmd = parts[0]
        args = parts[1:]
        if not native_only and is_cli:
            rlog = re.search(v.PIPE_PATTERN, log)
            if rlog is not None:
                self.parse_pipe(log)
                return
        match cmd:
            case "daemon":
                if not args:
                    man(manual="daemon_man")
                    return

                flag = args[0].lstrip("-").replace("-", "_")
                proc = daemon.find_daemon_process()

                handlers = {
                    "start": lambda: daemon.start(), "stop": lambda: daemon.stop(proc),
                    "status": lambda: daemon.status(proc), "logs": daemon.logs,
                    "rm_logs": daemon.rm_logs, "reboot": daemon.reboot,
                    "last_cmd": daemon.last_cmd, "disable": daemon.disable_logging,
                    "enable": daemon.enable_logging, "logging_status": daemon.logging_status,
                    "clear": daemon.clear_cmd,
                }
                if flag not in handlers:
                    print(f"Unknown flag: '{args[0]}'")
                    return
                handlers[flag]()
            case "ach":
                if not args:
                    man(manual="ach_man")
                    return
                flag = args[0].lstrip("-").replace("-", "_")
                handlers = {
                    "all": ach.all, "locked": ach.locked,
                    "unlocked": ach.unlocked
                }
                ach_id_pattern = re.match(v.ACH_ID_PATTERN, log)
                if flag in handlers:
                    handlers[flag]()
                elif ach_id_pattern:
                    achievements = ach_id_pattern.group(1)
                    achievements = shlex.split(achievements)
                    ach.achid(achievements)
                else:
                    print(f"Unknown flag: '{args[0]}'")
            case "shell":
                if not args:
                    man(manual="shell_man")
                    return
                flag = args[0].lstrip("-").replace("-", "_")
                handlers = {
                    "u": shell_.using, "select": shell_.select_util,
                }
                if flag in handlers:
                    handlers[flag]()
                else:
                    shell_pattern = re.search(v.SHELL_SELECT_PATTERN, log)
                    if shell_pattern:
                        shell = shell_pattern.group(1)
                        shell_.select(shell)
                    else:
                        print(f"Unknown flag: '{args[0]}'")

            case "h" | "help" | "man":
                man(manual="main")
            case "q" | "quit":
                v.running = False

            case "clear":
                subprocess.run(["clear"], stderr=subprocess.DEVNULL)

            case "install-config":
                install_conf.Installer.install_config()
            case "configs-all":
                self.configs_all()

            case "installed-configs":
                self.configs_installed()
                # Welcome screen
            case "fetch":
                fetch()
            case str() if cmd.startswith(":"):
                rlog = re.match(v.BASH_PATTERN, log)
                if rlog is not None:
                    self.parse_shell(rlog)
                    return
            case _:
                print(f"Uknown command: '{cmd}'.")

    # Function to parse bash commands (`:`)
    def parse_shell(self, log):
        # Get the command
        bash_command = log.group(1)
        if bash_command:
            try:
                with open(v.DATA_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                shell = data["shell"]
                if shell is not None:
                    # Executing
                    result = subprocess.run(
                        bash_command,
                        shell=True,
                        executable=shell,
                        text=True
                    )
                    # Printing an error if it is necessary
                    if result.returncode != 0:
                        print(result.stderr.strip())
                    return
                print("""Shell is not selected. Select a shell before running pipes or shell commands \
with 'shell --select' or shell shell_name""")
                return
            except Exception as e:
                print(f"{e}")

    # Function to parse pipes
    def parse_pipeline(self, log: str):
        log = log.strip()
        if not log:
            return []
        try:
            # Tokenize the string
            tokens = shlex.split(log, posix=False)
        except ValueError as e:
            print(f"Quotation mark parsing error: {e}")
            return [log]
        pipeline = []
        current_cmd = []
        for token in tokens:
            if token == "|":
                if current_cmd:
                    pipeline.append(" ".join(current_cmd))
                    current_cmd = []
            else:
                current_cmd.append(token)
        if current_cmd:
            pipeline.append(" ".join(current_cmd))

        return pipeline

    def parse_pipe(self, log):
        pipeline = self.parse_pipeline(log)
        if pipeline:
            # Native part
            native_part = pipeline[0]
            # Bash part
            pipe_part = pipeline[1:]
            # Intercept the stdout to RAM buffer to transfer the first command output to bash pipe
            captured_output = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured_output
            try:
                # Parse native part
                self.parse(native_part, native_only=True)
            finally:
                # Restore the stdout back to the system terminal
                sys.stdout = old_stdout
            # Extract the captured text from the RAM buffer to feed it into the Bash pipe
            app_output_text = captured_output.getvalue()
            try:
                with open(v.DATA_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                shell = data["shell"]
                if shell is not None:
                    # Execute the target Bash command with redirected standard input (stdin)
                    process = subprocess.Popen(
                        pipe_part,
                        shell=True,
                        executable=shell,
                        stdin=subprocess.PIPE,
                        text=True
                    )
                    # Feed the captured output string into the running Bash process via pipe
                    process.communicate(input=app_output_text)
                    return
                print("""Shell is not selected. Select a shell before running pipes or shell commands \
                with 'shell --select' or shell shell_name""")
                return
            except Exception as e:
                print(f"{e}")

    def configs_installed(self):
        # Get player's data
        with open(v.DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Get shell data
        shell_data = data["configs_installed"]
        # Print info about installed configs
        any_installed = False
        for shell in shell_data:
            if shell_data[shell]:
                print(shell)
                any_installed = True
        if not any_installed:
            print("No configs installed. You can install using `install-config`")

    # Function to print info about configs
    def configs_all(self):
        # Get player's data
        with open(v.DATA_PATH, "r", encoding='utf-8') as f:
            data = json.load(f)
        # Get shell data
        shell_data = data["configs_installed"]
        # Print info about every shell
        for shell in shell_data:
            print(f"Shell: {shell}. Installed: {shell_data[shell]}")  # configs[i] = True | False


class Shell:
    def __init__(self):
        pass

    def using(self):
        with open(v.DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data["shell"] is not None:
            shell_path = pathlib.Path(data["shell"])
            print(f"{shell_path.name} ({shell_path})")
            return
        print(f"Shell is not selected. You can select it with 'shell --select' \
or 'shell shell_name' (bash, zsh, fish are supported)")
    def select_util(self):
        print("This script selects a shell for using shell commands")
        print("Type 'q' or 'quit' to quit")
        while True:
            try:
                time.sleep(0.01)
                shell = input("(shell) Which shell would you like to use (bash, zsh or fish)? > ")
                match shell:
                    case "bash" | "zsh" | "fish":
                        ans = input(f"(shell) Are you sure you want to select {shell} [Y/n] > ")
                        if ans.lower() == "y" or ans == "":
                            if shell == "bash":
                                v.CURRENT_SHELL = v.BASH_BINARY_PATH
                            elif shell == "zsh":
                                v.CURRENT_SHELL = v.ZSH_BINARY_PATH
                            else:
                                v.CURRENT_SHELL = v.FISH_BINARY_PATH
                            with open(v.DATA_PATH, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            data["shell"] = str(v.CURRENT_SHELL)
                            with open(v.DATA_PATH, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=4)
                            print(f"{shell.capitalize()} successfully selected as a default shell.")
                            return
                    case "q" | "quit":
                        print("\nQuiting...")
                        return
                    case unknown:
                        print(f"Unknown shell typed: {unknown}")
            except KeyboardInterrupt:
                print("\nQuiting...")
                return
    def select(self, shell):
        with open(v.DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        match shell:
            case "bash" | "zsh" | "fish":
                if shell == "bash":
                    v.CURRENT_SHELL = v.BASH_BINARY_PATH
                elif shell == "zsh":
                    v.CURRENT_SHELL = v.ZSH_BINARY_PATH
                else:
                    v.CURRENT_SHELL = v.FISH_BINARY_PATH
                current_shell = str(v.CURRENT_SHELL)
                if current_shell != data["shell"]:
                    data["shell"] = current_shell
                    with open(v.DATA_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"{shell.capitalize()} successfully selected as a default shell")
                    return
                print(f"You already use {shell} as a default shell")
            case "reset":
                if data["shell"] is not None:
                    data["shell"] = None
                    with open(v.DATA_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print("Shell reset successfully")
                    return
                print("Shell is already reset")

            case unknown:
                print(f"Unknown shell typed: {unknown}")



class Ach:
    def __init__(self):
        pass
    def all(self):
        print("Printing the list of entire achievements...")
        with open(v.ACHIEVEMENT_PATH, "r", encoding='utf-8') as f:
            achs = json.load(f)

        with open(v.DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        achievements = achs

        for i in achievements:
            if not achievements[i]["secret"]:
                print(f"""Achievement: {achievements[i]["id"]}
Title: {achievements[i]["title"]} 
Description: {achievements[i]["description"]}
Difficulty: {achievements[i]["diff"]}
Done: {data["achievements"][i]["done"]}""")

    def locked(self):
        count_u = 0
        count = 0
        print("Printing the list of locked achievements...")
        with open(v.ACHIEVEMENT_PATH, "r", encoding='utf-8') as f:
            achs = json.load(f)

        with open(v.DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        achievements = achs

        for i in achievements:
            count += 1
            if not data["achievements"][i]["done"]:
                print(f"""Achievement: {achievements[i]["id"]}
Title: {achievements[i]["title"]}")
Description: {achievements[i]["description"]}
Difficulty: {achievements[i]["diff"]}""")
                count_u += 1

        print(f"Total locked: {count_u}/{count}")

    def unlocked(self):
        count_u = 0
        count = 0
        print("Printing the list of unlocked achievements...")
        with open(v.ACHIEVEMENT_PATH, "r", encoding='utf-8') as f:
            achs = json.load(f)

        with open(v.DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        achievements = achs

        for i in achievements:
            count += 1
            if data["achievements"][i]["done"]:
                print(f"""Achievement: {achievements[i]["id"]}
Title: {achievements[i]["title"]}")
Description: {achievements[i]["description"]}
Difficulty: {achievements[i]["diff"]}""")
                count_u += 1
        if count_u:
            print(f"Total unlocked: {count_u}/{count}")
            return
        print("It seems you have not unlocked any achievements yet")

    def achid(self, id: list):
        with open(v.ACHIEVEMENT_PATH, "r", encoding='utf-8') as f:
            achs = json.load(f)
        id_status = dict.fromkeys(id, False)
        with open(v.DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        achievements = achs
        for achievement in achievements:
            for ach in id:
                if achievement == ach:
                    print(f"""Achievement: {achievements[achievement]["id"]}
Title: {achievements[achievement]["title"]}
Description: {achievements[achievement]["description"]}
Difficulty: {achievements[achievement]["diff"]}
Unlocked: {data["achievements"][achievement]["done"]}
Secret: {achs[achievement]["secret"]}\n""")
                    id_status[ach] = True
        for achievement in id_status:
            if not id_status[achievement]:
                print(f"Could not find an achievement/flag: '{achievement}'")


class Daemon:
    def __init__(self):
        pass
    def find_daemon_process(self) -> psutil.Process | None:
        target = pathlib.Path(v.DAEMON_BIN_PATH).resolve()
        live, deleted = None, None
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                info = proc.info
                if info["name"] != v.DAEMON_NAME:
                    continue
                exe = info.get("exe")
                if not exe or exe is None:
                    continue

                is_deleted = exe.endswith(" (deleted)")
                exe_path = pathlib.Path(exe.replace(" (deleted)", "")).resolve()
                if exe_path != target:
                    continue
                if is_deleted:
                    deleted = deleted or proc
                else:
                    live = live or proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return live or deleted

    def stop(self, proc: psutil.Process | None):
        if proc is None:
            self.write_pid(None)
            print("Unavailable to terminate: it is not running")
            return
        print(f"Stopping daemon (PID: {proc.pid})...")
        try:
            proc.terminate()
            proc.wait(timeout=5)
            print("[+] Daemon successfully terminated.")
        except psutil.TimeoutExpired:
            print("[!] Terminating is taking too long. Killing forcibly...")
            try:
                proc.kill()
                proc.wait()
            except psutil.NoSuchProcess:
                pass
            print("[+] Daemon successfully terminated.")
        except psutil.NoSuchProcess:
            print("[-] Process is already terminated.")
            self.write_pid(None)
        except psutil.AccessDenied:
            print("[!] Access denied: cannot terminate the daemon (not enough privileges?)")
            return
        except Exception as e:
            print(f"[!] Unexpected error while stopping daemon: {e}")
            return
        self.write_pid(None)

    def start(self, reboot=False):
        proc = self.find_daemon_process()
        if proc:
            print(f"[-] Daemon is already running (PID: {proc.pid}).")
            self.write_pid(proc.pid)  # синхронизируем кэш
            return
        try:
            with open(os.devnull, "r") as devnull_in, \
                    open(v.LOG_FILE_PATH, 'w', encoding='utf-8', buffering=1) as log_out:
                proc = subprocess.Popen(
                    [str(v.DAEMON_BIN_PATH)],
                    stdin=devnull_in,
                    stdout=log_out,
                    stderr=log_out,
                    start_new_session=True, )

            self.write_pid(proc.pid)
            if not reboot:
                print(f"[+] Daemon successfully started in background (PID: {proc.pid}).")
            else:
                print(f"[+] Daemon successfully rebooted and started in background (PID: {proc.pid}).")
        except FileNotFoundError:
            print(f"[!] Error: Binary file not found at {v.DAEMON_BIN_PATH}")
        except Exception as e:
            prefix = "rebooting daemon" if reboot else "starting daemon"
            print(f"[!] Unexpected error while {prefix}: {e}")

    def reboot(self):
        proc = self.find_daemon_process()
        self.stop(proc)
        self.start(reboot=True)

    def write_pid(self, pid):
        if pid is None:
            return
        v.DAEMON_PID_PATH.parent.mkdir(parents=True, exist_ok=True)
        v.DAEMON_PID_PATH.write_text(str(pid), encoding="utf-8")

    def status(self, proc: psutil.Process | None):
        if proc is not None:
            print(f"[•] Status: RUNNING (PID: {proc.pid})")
            return
        print("[•] Status: STOPPED (daemon is not running)")
        self.write_pid(None)

    def disable_logging(self):
        if os.path.exists(v.PATH_DISABLED):
            print("[-] Cannot disable logging: it is already disabled")
            return
        os.makedirs(os.path.dirname(os.path.abspath(v.PATH_DISABLED)), exist_ok=True)
        with open(v.PATH_DISABLED, "w"):
            pass
        print("[+] Logging disabled successfully")
    def enable_logging(self):
        if not os.path.exists(v.PATH_DISABLED):
            print("[+] Cannot enable logging: it is already enabled")
            return
        v.PATH_DISABLED.unlink()
        print("[+] Logging enabled successfully")
    def logging_status(self):
        if os.path.exists(v.PATH_DISABLED):
            print("[•] LOGGING STATUS: disabled")
            return
        print("[•] LOGGING STATUS: enabled")
    def last_cmd(self):
        with open(v.PATH_LCMD, "r", encoding="utf-8") as log_file:
            logs = log_file.read().strip()
        print(logs)

    def rm_logs(self):
        with open(v.LOG_FILE_PATH, "w", encoding='utf-8') as logs:
            logs.write("")
        print("Successfully cleared the log file")

    def clear_cmd(self):
        with open(v.PATH_LCMD, "w") as f:
            f.write("")
        print("Successfully cleared!")

    def logs(self):
        try:
            if os.path.getsize(v.LOG_FILE_PATH) == 0:
                print("The file is empty")
                return
        except FileNotFoundError:
            # Touch the file if it does not exist
            pathlib.Path(v.LOG_FILE_PATH).touch()
            print("The file did not exist, but has been touched")
        with open(v.LOG_FILE_PATH, "r", encoding='utf-8') as f:
            logs = f.readlines()

        for i in logs:
            print(i.strip())
parser = Parser()
daemon = Daemon()
ach = Ach()
shell_ = Shell()

def fetch():
    print("""
    ###           ###    ###    ###    ###    ###   ###    ###         ####         ######      ###    ###   ###    #########    ###    ###    #########    ###      ###    #########   ###    ###  #########    ########
    ###           ###    ###    ###    ###    ###    ###  ###         ######      ##########    ###    ###   ###    #########    ###    ###    #########    ####     ###    #########   ###    ###  #########   ##########
    ###           ###    #####  ###    ###    ###     ######         ###  ###     ###    ###    ###    ###   ###    ###          ###    ###    ###          ############    ###         #####  ###     ###      ###
    ###           ###    ##########    ###    ###      ####         ##########    ###           ##########   ###    #########     ###  ###     #########    ###  ##  ###    #########   ##########     ###       #########
    ###           ###    ###  #####    ###    ###     ######        ##########    ###     ##    ##########   ###    #########      ######      #########    ###      ###    ###         ###  #####     ###        ########
    ###           ###    ###    ###    ###    ###    ###  ###       ###    ###    ###     ##    ###    ###   ###    ###             ####       ###          ###      ###    ###         ###    ###     ###      #      ###
    ##########    ###    ###    ###     ########    ###    ###      ###    ###    ##########    ###    ###   ###    #########       ####       #########    ###      ###    #########   ###    ###     ###     ####   ####
    ##########    ###    ###    ###      ######     ###    ###      ###    ###      ######      ###    ###   ###    #########        ##        #########    ###      ###    #########   ###    ###     ###      #########
                    """)
    print('''Welcome to Linux Achievements! Linux Achievements is a fully open-source (free) software, \
adding achievements into your GNU/Linux system and licensed funder AGPLv3 or later. 
Check my github: https://github.com/SIBDuck. Check repository: https://github.com/SIBDuck/linux-achievements
Here you can check your achievements and track your progress.
Type <h>, <help> or <man> for help, type <install-config> to install a shell script for logging commands''')

def man(manual=None):
    manuals = {
        "daemon_man": """Possible actions with 'daemon':
'daemon --start' - start the daemon
'daemon --stop' - stop the daemon 
'daemon --reboot' - reboot the daemon
'daemon --status' - print the daemon status
'daemon --logs' - print logs
'daemon --rm-logs' - delete logs
'daemon --enable' - enable logging
'daemon --disable' - disable logging
'daemon --last-cmd' - print the last command
'daemon --logging-status' - print logging status
'daemon --clear' - clear the last command log""",

        "ach_man": """Possible actions with 'ach':
ach --all - print all achievements
ach --locked - print locked achievements
ach --unlocked - print opened achievements
ach 'ID' - print info about an achievement (you do not have to use quotation marks, but you can)""",

        "shell_man": """Possible actions with 'shell':"
shell -u - print a selected shell for using bash commands here
shell --select - select a shell for using bash commands here (interactive utility)
shell shell_name - select the shell for using bash commands here (bash, zsh and fish are supported)
shell reset - reset the shell"""
    }

    man_all = f"""'help'/'h'/'man' - print this menu
install-config' - install a shell script for logging commands
'configs-installed' - print info about installed configs for the shells
'configs-all' - print info about shells and configs for them
{manuals["daemon_man"]}
{manuals["ach_man"]}
{manuals["shell_man"]}
'clear' - clear the screen
'fetch' - print the welcome screen
use ':' to use bash commands like in vim (pipes with utility-commands are supported)
Hint: you could use 'more' and 'less' if you want to see a big list of something (e.g.: ach --all | more)
'q'/'quit' - quit this program"""
    if manual in manuals.keys():
        print(manuals[manual])
        return
    print(man_all)


def main():
    if "TERM" not in os.environ or not os.environ["TERM"]:
        os.environ["TERM"] = "xterm-256color"

    fetch()

    while v.running:
        try:
            inp = input("> ")
            parser.parse(inp)
        except KeyboardInterrupt:
            break
    print("\nGoodbye...")


if __name__ == "__main__":
    main()
