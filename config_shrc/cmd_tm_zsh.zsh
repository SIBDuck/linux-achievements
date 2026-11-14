#!/bin/zsh

# Copyright (C) 2026 SIBDuck
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://gnu.org>.

# ==============================================================================
# WARNING & SECURITY NOTICE:
# - This script logs the last terminal command
# - Use strictly at your own risk. The author assumes no liability for leaks.
#==============================================================================


# Load the built-in time module (runs completely in memory without spawning a subshell)
zmodload zsh/datetime 2>/dev/null

# State flag (0 = idle/free, 1 = editor session currently active)
_ACH_EDITOR_ACTIVE=0

# Path to the current user's isolated runtime RAM directory
_ACH_RAM_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/linux-achievements"
_ACH_LOG_FILE="$_ACH_RAM_DIR/last_cmd"

# Regular expression matching PCRE standards (Zsh) to identify text editors (supports sudo, flags, paths)
_ACH_ED_REGEX='^([[:space:]]*sudo([[:space:]]+-[a-zA-Z0-9]+([[:space:]]+[^[:space:]]+)?)?[[:space:]]+)?([^[:space:]]*/)?(vi|vim|nvim|nano|emacs|mcedit|gedit|kate|micro|visudo|sudoedit)([[:space:]]|$)'

# Initialize the RAM directory and determine the system's default text editor
if mkdir -p "$_ACH_RAM_DIR" 2>/dev/null; then
    _ed="${EDITOR:-nano}"
    _ed="${_ed%% *}"
    _ed="${_ed##*/}"
    printf "%s\n" "$_ed" > "$_ACH_RAM_DIR/editor" 2>/dev/null
fi

# Hook 1: Executed IMMEDIATELY BEFORE command execution (Triggers START status exclusively for text editors)
_log_achievements_preexec() {
    # Early exit if the logging mechanism is explicitly disabled by the utility
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return
    (( _ACH_EDITOR_ACTIVE == 1 )) && return

    local current_cmd="$1"
    # Ignore empty commands and internal telemetry tracking utilities
    [[ -z "$current_cmd" || "$current_cmd" == *"_log_achievements"* ]] && return

    # Dynamically load the Zsh PCRE engine for regex matching
    zmodload zsh/pcre 2>/dev/null

    if [[ "$current_cmd" =~ $_ACH_ED_REGEX ]]; then
        _ACH_EDITOR_ACTIVE=1
        _CURRENT_RAW_CMD="$current_cmd"
        mkdir -p "$_ACH_RAM_DIR" 2>/dev/null

        # Log structure: [EPOCH_TIMESTAMP] START [RAW_COMMAND]
        # Uses built-in $EPOCHSECONDS for instant execution without invoking /bin/date
        printf "%s START %s\n" "$EPOCHSECONDS" "$current_cmd" > "$_ACH_LOG_FILE" 2>/dev/null
    fi
}

# Hook 2: Executed AFTER command completion (Logs the END status and exit code for all commands)
_log_achievements_precmd() {
    local exit_code=$?

    # Early exit if the logging mechanism is explicitly disabled by the utility
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return

    # Fetch the latest entry from Zsh history buffer (-n flag suppresses line numbers)
    local last_cmd
    last_cmd=$(fc -ln -1 -1 2>/dev/null)
    last_cmd=$(echo "$last_cmd" | xargs)

    # Ignore empty commands and internal tracking utilities
    [[ -z "$last_cmd" || "$last_cmd" == *"_log_achievements"* ]] && return

    # Reset the active editor state flag
    _ACH_EDITOR_ACTIVE=0

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null

    # Log structure: [EPOCH_TIMESTAMP] END [EXIT_CODE] [CLEANED_COMMAND]
    # Uses built-in $EPOCHSECONDS for high performance
    printf "%s END %s %s\n" "$EPOCHSECONDS" "$exit_code" "$last_cmd" > "$_ACH_LOG_FILE" 2>/dev/null
}

# Hook 3: Fallback executed if the terminal window is closed unexpectedly (e.g., SIGHUP/window X button) during active editing
_log_achievements_zsh_exit() {
    # Early exit if logging is disabled or no text editor session was running
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return
    (( _ACH_EDITOR_ACTIVE == 0 )) && return

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null

    # Log the abrupt termination with a standard exit code 129 (SIGHUP)
    printf "%s END 129 %s\n" "$EPOCHSECONDS" "$_CURRENT_RAW_CMD" > "$_ACH_LOG_FILE" 2>/dev/null
    _ACH_EDITOR_ACTIVE=0
}

# Register the standard Zsh execution hooks via the autoload framework
autoload -Uz add-zsh-hook
add-zsh-hook preexec _log_achievements_preexec
add-zsh-hook precmd _log_achievements_precmd

# Register the fallback exit trap
trap '_log_achievements_zsh_exit' EXIT
