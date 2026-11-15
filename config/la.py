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
# TODO: redirecting, add exit code mechanic (fucntion above main())
import time
import subprocess
import pathlib
import os
import re
import sys
import io
import json
import atexit
from achievement_manager import manager as mgr
import install_conf
import variables as v
import psutil
import shlex

# TODO: add redirecting
class Parser:
    def __init__(self):
        pass

    def parse(self, log, native_only=False, is_cli=True):
        try:
            parts = shlex.split(log)
            if not parts:
                return 0
        except ValueError as e:
            print(f"{e}")
            return 130

        cmd = parts[0]
        args = parts[1:]
        if not native_only and is_cli:
            rlog = re.search(v.PIPE_PATTERN, log)
            if rlog is not None:
                ec = self.parse_pipe(log)
                return ec
        match cmd:
            case "daemon":
                if not args:
                    man(manual="daemon_man")
                    return 2

                flag = args[0].strip().replace("-", "_")
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
                    print(f"Unknown flag: '{args[0]}'", file=sys.stderr)
                    return 2
                ec = handlers[flag]()
                return ec
            case "ach":
                if not args:
                    man(manual="ach_man")
                    return 2
                flag = args[0].lstrip("-").replace("-", "_")
                handlers = {
                    "all": ach.all, "locked": ach.locked,
                    "unlocked": ach.unlocked
                }
                ach_id_pattern = re.match(v.ACH_ID_PATTERN, log)
                if flag in handlers:
                    ec = handlers[flag]()
                elif ach_id_pattern:
                    achievements = ach_id_pattern.group(1)
                    achievements = shlex.split(achievements)
                    ec = ach.achid(achievements)
                else:
                    print(f"Unknown flag: '{args[0]}'", file=sys.stderr)
                    return 2
                return ec
            case "shell":
                if not args:
                    man(manual="shell_man")
                    return 2
                flag = "".join(args)
                handlers = {
                    "-u": shell_.using, "--select": shell_.select_util,
                }
                if flag in handlers:
                    ec = handlers[flag]()
                else:
                    shell_pattern = re.search(v.SHELL_SELECT_PATTERN, log)
                    if shell_pattern:
                        shell = shell_pattern.group(1)
                        ec = shell_.select(shell)
                    else:
                        print(f"Unknown flag: '{args[0]}'", file=sys.stderr)
                        return 2
                return ec

            case "dbg":
                handlers = {"check": debugger.check_files}
                flag = args[0]
                if len(args) == 1 and args[0] in handlers:
                    ec = handlers[flag]()
                    return ec
                if flag != "":
                    print(f"Unknown argument: '{flag}'", file=sys.stderr)
                    return 2
                man(manual="dbg_man")
                return 2

            case "h" | "help" | "man":
                handlers = ["daemon", "ach", "shell", "main", "dbg"]
                manuals = args
                has_error = False
                if not manuals:
                    man(manual="main")
                    return 0
                for index, manual in enumerate(manuals):
                    if manual not in handlers:
                        print(f"Uknown manual: '{manual}'", file=sys.stderr)
                        has_error = True
                        continue
                    if manual != "main":
                        mn = manual + "_man"
                        man(manual=mn)
                        if index < len(manuals) - 1:
                            print()
                        continue
                    man(manual="main")
                return 0 if not has_error else 1

            case "q" | "quit":
                v.running = False
                return 0

            case "clear":
                subprocess.run(["clear"], stderr=subprocess.DEVNULL)
                return 0

            case "install-config":
                ec = install_conf.installer.install_config()
                return ec
            case "configs-all":
                ec = self.configs_all()
                return ec

            case "installed-configs":
                ec = self.configs_installed()
                return ec
                # Welcome screen
            case "fetch":
                fetch()
                return 0
            case str() if cmd.startswith(":"):
                rlog = re.match(v.BASH_PATTERN, log)
                if rlog is not None:
                    ec = self.parse_shell(rlog)
                    return ec
            case _:
                print(f"Unknown command: '{cmd}'", file=sys.stderr)
                return 2

    # Function to parse bash commands (`:`)
    def parse_shell(self, log):
        # Get the command
        shell_command = log.group(1)
        if shell_command is None:
            return 0
        try:
            with open(v.DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            shell = data["shell"]

        except Exception as e:
            print(f"Config error: {e}", file=sys.stderr)
            return 1

        if shell is None:
            print("""Shell is not selected. Select a shell before running shell commands \
with 'shell --select' or shell shell_name""", file=sys.stderr)
            return 1
        try:
             # Executing
            result = subprocess.run(
                shell_command,
                shell=True,
                executable=shell,
                text=True
                )
            return result.returncode
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    # Function to parse pipes
    def parse_pipeline(self, log: str):
        log = log.strip()
        if not log:
            return []
        try:
            # Tokenize the string
            tokens = shlex.split(log, posix=False)
        except ValueError as e:
            print(f"Quotation mark parsing error: {e}", file=sys.stderr)
            return [log]
        pipeline = []
        current_cmd = []
        for token in tokens:
            if token == "|":
                if current_cmd:
                    pipeline.append(shlex.join(current_cmd))
                    current_cmd = []
            else:
                current_cmd.append(token)
        if current_cmd:
            pipeline.append(shlex.join(current_cmd))

        return pipeline

    def parse_pipe(self, log):
        pipeline = self.parse_pipeline(log)
        if not pipeline:
            return 0
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
        except Exception as e:
            print(f"Config error: {e}", file=sys.stderr)
            return 1

        if shell is None:
            print("""Shell is not selected. Select a shell before running shell commands \
with 'shell --select' or shell shell_name""", file=sys.stderr)
            return 1
        try:
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
            return process.returncode
        except BrokenPipeError as e:
            print(f"{e}", file=sys.stderr)
            return 141
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    def configs_installed(self):
        # Get player's data
        try:
            with open(v.DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Get shell data
            shell_data = data["configs_installed"]
            # Print info about installed configs
        except Exception as e:
            print(f"Config error: {e}", file=sys.stderr)
            return 1
        any_installed = False
        for shell in shell_data:
            if shell_data[shell]:
                print(shell)
                any_installed = True
        if not any_installed:
            print("No configs installed. You can install using `install-config`", file=sys.stderr)
            return 1
        return 0

    # Function to print info about configs
    def configs_all(self):
        # Get player's data
        try:
            with open(v.DATA_PATH, "r", encoding='utf-8') as f:
                data = json.load(f)
            # Get shell data
            shell_data = data["configs_installed"]
        except Exception as e:
            print(f"Config error: {e}", file=sys.stderr)
            return 1
        # Print info about every shell
        for shell in shell_data:
            print(f"Shell: {shell}. Installed: {shell_data[shell]}")  # configs[i] = True | False
        return 0


class Shell:
    def __init__(self):
        pass

    def using(self):
        try:
            with open(v.DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data["shell"] is None:
                print(f"Shell is not selected. You can select it with 'shell --select' \
            or 'shell shell_name' (bash, zsh, fish are supported)", file=sys.stderr)
                return 1
            shell_path = pathlib.Path(data["shell"])
            print(f"{shell_path.name} ({shell_path})")
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1


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
                            return 0
                    case "q" | "quit":
                        print("\nQuiting...")
                        return 0
                    case unknown:
                        print(f"Unknown shell typed: {unknown}", file=sys.stderr)


            except KeyboardInterrupt:
                print("\nQuiting...")
                return 0
            except Exception as e:
                print(f"{e}", file=sys.stderr)
                return 1

    def select(self, shell):
        try:
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
                        return 0
                    print(f"You already use {shell} as a default shell", file=sys.stderr)
                    return 0
                case "reset":
                    data["shell"] = None
                    with open(v.DATA_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print("Shell reset successfully")
                    return 0
                case unknown:
                    print(f"Unknown shell typed: '{unknown}'", file=sys.stderr)
                    return 1
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1


class Ach:
    def __init__(self):
        pass

    def all(self):
        try:
            count = 0
            print("Printing the list of entire achievements...")
            with open(v.ACHIEVEMENT_PATH, "r", encoding='utf-8') as f:
                achs = json.load(f)

            with open(v.DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)

            achievements = achs

            for i in achievements:
                count += 1
                if not achievements[i]["secret"] or achievements[i]["secret"] and achievements[i]["done"]:
                    print(f"""Achievement: {achievements[i]["id"]}
Title: {achievements[i]["title"]} 
Description: {achievements[i]["description"]}
Difficulty: {achievements[i]["diff"]}
Done: {data["achievements"][i]["done"]}\n""")
                elif achievements[i]["secret"] and not achievements[i]["done"]:
                    print(f"""Achievement: {"*"*len(achievements[i]["id"])}
Title: {achievements[i]["title"]}
Description: ********
Difficulty: {achievements[i]["diff"]}
Done: {data["achievements"][i]["done"]}\n""")
            print(f"Total: {count}")
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    def locked(self):
        try:
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
Difficulty: {achievements[i]["diff"]}\n""")
                    count_u += 1

            print(f"Total locked: {count_u}/{count}")
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    def unlocked(self):
        try:
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
Difficulty: {achievements[i]["diff"]}\n""")
                    count_u += 1
            if count_u:
                print(f"Total unlocked: {count_u}/{count}")
            print("It seems you have not unlocked any achievements yet")
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    def achid(self, id: list):
        ec = 0
        try:
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
                    print(f"Could not find an achievement or flag: '{achievement}'", file=sys.stderr)
                    ec = 1
            return ec
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1


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
            print("Unavailable to terminate: it is not running", file=sys.stderr)
            return 1
        print(f"Stopping daemon (PID: {proc.pid})...")
        try:
            proc.terminate()
            proc.wait(timeout=5)
            print("[+] Daemon successfully terminated.")
            ec = 0
        except psutil.TimeoutExpired:
            print("[!] Terminating is taking too long. Killing forcibly...")
            try:
                proc.kill()
                proc.wait()
            except psutil.NoSuchProcess:
                pass
            print("[+] Daemon successfully terminated.")
            ec = 0
        except psutil.NoSuchProcess:
            print("[-] Process is already terminated.", file=sys.stderr)
            self.write_pid(None)
            ec = 1
        except psutil.AccessDenied:
            print("[!] Access denied: cannot terminate the daemon (not enough privileges?)", file=sys.stderr)
            ec = 1
        except Exception as e:
            print(f"[!] Unexpected error while stopping daemon: {e}", file=sys.stderr)
            ec = 1
        self.write_pid(None)
        return ec

    def start(self, reboot=False):
        proc = self.find_daemon_process()
        if proc:
            print(f"[-] Daemon is already running (PID: {proc.pid}).", file=sys.stderr)
            self.write_pid(proc.pid)
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
            return 0
        except FileNotFoundError:
            print(f"[!] Error: Binary file not found at {v.DAEMON_BIN_PATH}", file=sys.stderr)
            return 1
        except Exception as e:
            prefix = "rebooting daemon" if reboot else "starting daemon"
            print(f"[!] Unexpected error while {prefix}: {e}", file=sys.stderr)
            return 1

    def reboot(self):
        proc = self.find_daemon_process()
        ec0 = self.stop(proc)
        ec1 = self.start(reboot=True)
        return 0 if (ec0 == 0 and ec1 == 0) else 1

    def write_pid(self, pid):
        if pid is None:
            return
        v.DAEMON_PID_PATH.parent.mkdir(parents=True, exist_ok=True)
        v.DAEMON_PID_PATH.write_text(str(pid), encoding="utf-8")

    def status(self, proc: psutil.Process | None):
        if proc is not None:
            print(f"[•] Status: RUNNING (PID: {proc.pid})")
            return 0
        print("[•] Status: STOPPED (daemon is not running)")
        self.write_pid(None)
        return 0

    def disable_logging(self):
        if os.path.exists(v.PATH_DISABLED):
            print("[-] Cannot disable logging: it is already disabled", file=sys.stderr)
            return 1
        os.makedirs(os.path.dirname(os.path.abspath(v.PATH_DISABLED)), exist_ok=True)
        with open(v.PATH_DISABLED, "w"):
            pass
        print("[+] Logging disabled successfully")
        return 0

    def enable_logging(self):
        if not os.path.exists(v.PATH_DISABLED):
            print("[+] Cannot enable logging: it is already enabled", file=sys.stderr)
            return 1
        v.PATH_DISABLED.unlink()
        print("[+] Logging enabled successfully")
        return 0

    def logging_status(self):
        if os.path.exists(v.PATH_DISABLED):
            print("[•] Status: disabled")
        else: print("[•] Status: enabled")
        return 0

    def last_cmd(self):
        try:
            with open(v.PATH_LCMD, "r", encoding="utf-8") as log_file:
                logs = log_file.read().strip()
            print(logs)
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    def rm_logs(self):
        try:
            with open(v.LOG_FILE_PATH, "w", encoding='utf-8') as logs:
                logs.write("")
            print("Successfully cleared the log file")
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    def clear_cmd(self):
        try:
            with open(v.PATH_LCMD, "w") as f:
                f.write("")
            print("Successfully cleared!")
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1

    def logs(self):
        try:
            if os.path.getsize(v.LOG_FILE_PATH) == 0:
                print("The file is empty")
                return 0
            with open(v.LOG_FILE_PATH, "r", encoding='utf-8') as f:
                logs = f.readlines()
            for i in logs:
                print(i.strip())
            return 0
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            return 1



class History:
    def __init__(self):
        pass
    def _clear_cli(self) -> None:
        _cli_history_fd.seek(0)
        _cli_history_fd.truncate(0)
        _cli_history_fd.flush()
    def _clear_shell(self) -> None:
        v.LASH_HISTORY_SHELL.write_text("", encoding="utf-8")

    def clear(self, arg: str = "") -> None:
        success = False
        if not arg:
            self._clear_shell()
            self._clear_cli()
        elif arg == "cli":
            self._clear_cli()
        elif arg == "shell":
            self._clear_shell()
        else:
            print(f"Unknown argument: '{arg}'", file=sys.stderr)
class Debugger:
    def __init__(self):
        pass
    def check_files(self):
        created = init_ram_dir()
        if created:
            print("[+] Missing files and folders created successfully")
            return 0
        print("[+] Everything is OK")
        return 0

class Profile:
    def __init__(self):
        pass
    def profile(self):
        pass


parser = Parser()
daemon = Daemon()
ach = Ach()
shell_ = Shell()
history = History()
debugger = Debugger()

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
adding achievements into your GNU/Linux system and licensed under AGPLv3 or later. 
Check my github: https://github.com/SIBDuck. Check repository: https://github.com/SIBDuck/linux-achievements
Here you can check your achievements and track your progress.
Type <h>, <help> or <man> for help, type <install-config> to install a shell script for logging commands''')


def man(manual=None):
    manuals = {
        "daemon_man": """Possible actions with 'daemon':
'daemon start' - start the daemon
'daemon stop' - stop the daemon
'daemon reboot' - reboot the daemon
'daemon status' - print the daemon status
'daemon logs' - print logs
'daemon rm-logs' - delete logs
'daemon enable' - enable logging
'daemon disable' - disable logging
'daemon last-cmd' - print the last command
'daemon logging-status' - print logging status
'daemon clear' - clear the last command log""",

        "ach_man": """Possible actions with 'ach':
'ach --all' - print all achievements
'ach --locked' - print locked achievements
'ach --unlocked' - print opened achievements
'ach "ID"' - print info about an achievement (quotation marks are unnecessary)""",

        "shell_man": """Possible actions with 'shell':
'shell -u' - print a selected shell for using bash commands here
'shell --select' - select a shell for using bash commands here (interactive utility)
'shell shell_name' - select the shell for using bash commands here (bash, zsh and fish are supported)
'shell reset' - reset the shell""",
        "history_man": """Possible actions with 'history':
'history -c <arguments>' - clears history of utility commands, arguments (unnecessary): shell|cli, if not arguments - clears the whole history)
        """,
        "dbg_man": """Possible actions with 'dbg':
'dbg check' - check if files and folders needed for daemon working exist"""
    }

    man_all = f"""'help'/'h'/'man' - print this menu
'install-config' - install a shell script for logging commands
'configs-installed' - print info about installed configs for the shells
'configs-all' - print info about shells and configs for them
{manuals["daemon_man"]}
{manuals["ach_man"]}
{manuals["shell_man"]}
{manuals["dbg_man"]}
'clear' - clear the screen
'fetch' - print the welcome screen
use ':' to use bash commands like in vim (pipes with utility-commands are supported)
Hint: you could use 'more' and 'less' if you want to see a big list of something (e.g.: ach --all | more)
'q'/'quit' - quit this program"""
    if manual in manuals:
        print(manuals[manual])
        return
    print(man_all)

def eprg(exit_code: int, is_cli=False):
    if not is_cli:
        sys.exit(exit_code)

def wh(cmd: str, is_cli=False, clear_his=False):
    if not cmd:
        return
    cmd = cmd.strip()
    if not is_cli:
        v.LASH_HISTORY_SHELL.touch(exist_ok=True)
        if not clear_his:
            with open(v.LASH_HISTORY_SHELL, "a", encoding="utf-8") as f:
                f.write(f"{cmd}\n")
        return
    if not clear_his:
        _cli_history_fd.write(f"{cmd}\n")

def init_ram_dir():
    what_to_return = False
    for path in [v.PATH_LCMD, v.PATH_EDITOR, v.DAEMON_PID_PATH, v.LOG_FILE_PATH]:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            what_to_return = True
    return what_to_return

v.LASH_HISTORY_CLI.touch(exist_ok=True)
_cli_history_fd = v.LASH_HISTORY_CLI.open("a", encoding="utf-8", buffering=1)
def main():
    if "TERM" not in os.environ or not os.environ["TERM"]:
        os.environ["TERM"] = "xterm-256color"
    last_ec = 0
    fetch()

    while v.running:
        try:
            inp = input("> ")
            if not inp.strip(): continue
            if inp.strip() in ("q", "quit"):
                break
            last_ec = parser.parse(inp)
            mgr.achievement_manager.cli_achs(inp)
            wh(inp, is_cli=True)
        except KeyboardInterrupt:
            print()
            return 130
        except EOFError:
            return 0
        except Exception as e:
            return 0
    print("\nGoodbye...")
    atexit.register(_cli_history_fd.close)
    return last_ec

if __name__ == "__main__":
    sys.exit(main())
