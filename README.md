# Linux Achievements
## What is this??
It is a fully free (open source) utility, adding achievements into your GNU/Linux system and licensed under [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html) ([what is AGPLv3](https://www.gnu.org/licenses/why-affero-gpl.html))! Your latest terminal command is logged and parsed in real time, to determine whether you unlock a new achievement.
## Is it safe?
Yes, it is absolutely safe. Your last command is written directly to `XDG_RUNTIME_DIR` (usually `/run/user/$(id -u)`). This directory is mounted as a tmpfs RAM drive, ensuring that only YOUR specific user has access to it. Your data is strictly local, requires no internet connection, and cannot be stolen!
## How to use??
### 1. Install the utility
The package is available in the **Arch User Repository** ([AUR](https://aur.archlinux.org/)). What is [AUR](https://wiki.archlinux.org/title/Arch_User_Repository)?
---
**Bash**
```console
# Install, using `paru`
paru -S linux-achievements 
# Install, using `yay`
yay -S linux-achievements
```

### 2. Run the utility
Run the utility (you can run it with `la` to launch CLI interface or with `la <command>`, use `la h` or `la help` to see comands)
You can interact with the software in two ways:
* **Interactive TUI Mode:** Just type `la` to open the fully featured interactive text interface, view your unlocked progress, and check difficulty levels.
* **Direct Command Mode:** Run single quick actions without entering the interface, for example:
---
**Bash**
```console
# Show the help menu with all available commands
la h
# Use utility commands without CLI interface
la <cmd>  
# Run CLI interface
la 
```

### 3. Shell Logging Setup
1. Run the built-in configuration installer:
---
**Bash**
```console
# Without CLI interface
la install-config 
# In CLI interface
install-config 
```

2. Follow the quick on-screen instructions to finalize the integration.

---

**That's it! Your terminal is now armed. Have fun completing hidden tasks, exploring new tools, and unlocking achievements! 🚀**
After that, utility is ready for using! Have fun, completing tasks to unlock achievements!

## 🛠️ Requirements

### Operating System
* **OS:** Arch Linux (x86_64)

### Supported Shells
The utility officially supports and hooks into the following shells:
* **Bash** (tested on 5.0+)
* **Zsh** (tested on 5.8+) — *requires `zsh/datetime` and `zsh/pcre` modules (built-in)*
* **Fish** (tested on 3.4+)

### System Dependencies
* **Init System:** Systemd — required to run the background tracking daemon (`lad`) as a user service.
* **Core Utilities:** `procps-ng` (provides `pgrep`) and `util-linux` (provides `fc` for Bash/Zsh history parsing).

### Python Environment (Internal / Build-time)
* **Python:** 3.10 or higher
