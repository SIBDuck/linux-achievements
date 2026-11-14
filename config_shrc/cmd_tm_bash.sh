#!/bin/bash

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

# State flag (0 = idle/free, 1 = editor session currently active)
_ACH_EDITOR_ACTIVE=0

# Path to the current user's isolated runtime RAM directory
_ACH_RAM_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/linux-achievements"
_ACH_LOG_FILE="$_ACH_RAM_DIR/last_cmd"

# Regular expression to quickly identify text editors (supports sudo, flags, paths, and common editors)
_ACH_ED_REGEX='^([[:space:]]*sudo([[:space:]]+-[a-zA-Z0-9]+([[:space:]]+[^[:space:]]+)?)?[[:space:]]+)?([^[:space:]]*/)?(vi|vim|nvim|nano|emacs|mcedit|gedit|kate|micro|visudo|sudoedit)([[:space:]]|$)'

# Initialize the RAM directory and determine the system's default text editor
if mkdir -p "$_ACH_RAM_DIR" 2>/dev/null; then
    _ed="${EDITOR:-nano}"
    _ed="${_ed%% *}"
    _ed="${_ed##*/}"
    printf "%s\n" "$_ed" > "$_ACH_RAM_DIR/editor" 2>/dev/null
fi

# Hook 1: Executed BEFORE a command runs (Triggers START status exclusively for text editors)
_log_achievements_start() {
    # Early exit if the logging mechanism is explicitly disabled by the utility
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return

    # Ignore empty commands, prompt expansions, internal hooks, and active editor subshells
    [[ -z "$BASH_COMMAND" || "$BASH_COMMAND" == "$PROMPT_COMMAND" ]] && return
    [[ "$BASH_COMMAND" == *"_log_achievements"* || "$BASH_COMMAND" == *"__vte"* ]] && return
    (( _ACH_EDITOR_ACTIVE == 1 )) && return

    # Check if the incoming command matches the editor regex using native Bash pattern matching
    if [[ "$BASH_COMMAND" =~ $_ACH_ED_REGEX ]]; then
        _ACH_EDITOR_ACTIVE=1
        _CURRENT_RAW_CMD="$BASH_COMMAND"
        mkdir -p "$_ACH_RAM_DIR" 2>/dev/null

        # Log structure: [TIMESTAMP] START [RAW_COMMAND]
        printf "%(%s)T START %s\n" "-1" "$BASH_COMMAND" > "$_ACH_LOG_FILE" 2>/dev/null
    fi
}

# Hook 2: Executed AFTER a command finishes (Logs the END status and exit code for all commands)
_log_achievements_bash() {
    local exit_code=$?

    # Early exit if the logging mechanism is explicitly disabled by the utility
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return
    [[ "$BASH_COMMAND" == "$PROMPT_COMMAND" ]] && return

    # Retrieve the last executed command line from Bash history
    local last_cmd
    last_cmd=$(history 1)

    # Strip the leading history line numbers added by Bash
    last_cmd="${last_cmd#*[0-9]*  }"
    # Trim leading and trailing whitespaces
    last_cmd=$(echo "$last_cmd" | xargs)

    # Ignore empty commands and internal tracking utilities
    [[ -z "$last_cmd" || "$last_cmd" == *"_log_achievements"* || "$last_cmd" == *"__vte"* ]] && return

    # Reset the active editor state flag
    _ACH_EDITOR_ACTIVE=0

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null
    # Log structure: [TIMESTAMP] END [EXIT_CODE] [CLEANED_COMMAND]
    printf "%(%s)T END %s %s\n" "-1" "$exit_code" "$last_cmd" > "$_ACH_LOG_FILE" 2>/dev/null
}

# Hook 3: Fallback executed if the terminal window is closed unexpectedly (e.g., SIGHUP/window X button) during active editing
_log_achievements_exit() {
    trap - DEBUG

    # Early exit if logging is disabled or no text editor session was running
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return
    (( _ACH_EDITOR_ACTIVE == 0 )) && return

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null
    # Log the abrupt termination with a standard exit code 129 (SIGHUP)
    printf "%(%s)T END 129 %s\n" "-1" "$_CURRENT_RAW_CMD" > "$_ACH_LOG_FILE" 2>/dev/null
    _ACH_EDITOR_ACTIVE=0
}

# Ensure DEBUG trap is inherited by functions and subshells
set +t

# Inject the post-command hook into PROMPT_COMMAND without breaking existing hooks
if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="_log_achievements_bash"
elif [[ "$PROMPT_COMMAND" != *"_log_achievements_bash"* ]]; then
    PROMPT_COMMAND="_log_achievements_bash; $PROMPT_COMMAND"
fi

# Register system hooks using native Bash traps
trap '_log_achievements_start' DEBUG
trap '_log_achievements_exit' EXIT
