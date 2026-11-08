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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# ==============================================================================
# WARNING & SECURITY NOTICE:
# - This script logs the last terminal command
# - Use strictly at your own risk. The author assumes no liability for leaks.
#==============================================================================

# State flag (0 = idle/free, 1 = editor session currently active)
set -g _ACH_EDITOR_ACTIVE 0

# Path to the current user's isolated runtime RAM directory
set -g _ACH_RAM_DIR (string join '/' (or $XDG_RUNTIME_DIR "/run/user/"(id -u)) "linux-achievements")
set -g _ACH_LOG_FILE "$_ACH_RAM_DIR/last_cmd"

# List of target text editors to monitor
set -g _ACH_EDITORS vi vim nvim nano emacs mcedit gedit kate micro visudo sudoedit

# Initialize the RAM directory and determine the system's default text editor
if mkdir -p $_ACH_RAM_DIR 2>/dev/null
    set -l _ed (or $EDITOR "nano")
    set _ed (string split ' ' $_ed)
    set _ed (basename $_ed[1])
    echo $_ed > "$_ACH_RAM_DIR/editor"
end

# Optimized helper function to parse the command string and isolate the primary executable binary
# Handled edge cases: skips over 'sudo' and any associated utility flags/parameters (e.g., -u user)
function _ach_get_binary
    set -l cmd_args (string split ' ' (string trim $argv))
    set -l idx 1
    while test $idx -le (count $cmd_args)
        if test "$cmd_args[$idx]" = "sudo"
            set idx (math $idx + 1)
            # Iterate through sudo options starting with a hyphen (-)
            while test $idx -le (count $cmd_args); and string match -r '^-' "$cmd_args[$idx]"
                # Flags requiring an extra argument (-u, -g, -p, -c) increment the index further
                if string match -r '^-[ugpc]$' "$cmd_args[$idx]"
                    set idx (math $idx + 2)
                else
                    set idx (math $idx + 1)
                end
            end
        else
            break
        end
    end
    if test $idx -le (count $cmd_args)
        basename $cmd_args[$idx]
    end
end

# Hook 1: Triggered BEFORE command execution (Logs START status exclusively for monitored text editors)
function _log_achievements_start --on-event fish_preexec
    # Early exit if the logging mechanism is explicitly disabled by the utility
    if test -f "$_ACH_RAM_DIR/disabled"; return; end
    if test "$_ACH_EDITOR_ACTIVE" -eq 1; return; end

    # Ignore internal tracking utilities
    if string match -q "*_log_achievements*" "$argv"; return; end

    # Extract the target binary from the full command string
    set -l clean_bin (_ach_get_binary "$argv")

    # If the resolved binary matches an entry in our monitored editors list
    if contains "$clean_bin" $_ACH_EDITORS
        set -g _ACH_EDITOR_ACTIVE 1
        set -g _CURRENT_RAW_CMD "$argv"
        mkdir -p $_ACH_RAM_DIR 2>/dev/null

        # Log structure: [UNIX_TIMESTAMP] START [RAW_COMMAND]
        printf "%s START %s\n" (date +%s) "$argv" > $_ACH_LOG_FILE 2>/dev/null
    fi
end

# Hook 2: Triggered AFTER command completion (Logs the END status and exit code for all commands)
function _log_achievements_bash --on-event fish_postexec
    set -l exit_code $status

    # Early exit if the logging mechanism is explicitly disabled by the utility
    if test -f "$_ACH_RAM_DIR/disabled"; return; end
    if string match -q "*_log_achievements*" "$argv"; return; end

    # Reset the active editor state flag
    set -g _ACH_EDITOR_ACTIVE 0
    mkdir -p $_ACH_RAM_DIR 2>/dev/null
    set -l last_cmd (string trim "$argv")

    # Log structure: [UNIX_TIMESTAMP] END [CLEANED_COMMAND] [EXIT_CODE]
    printf "%s END %s %s\n" (date +%s) "$last_cmd" $exit_code > $_ACH_LOG_FILE 2>/dev/null
end

# Hook 3: Fallback triggered when the terminal shell process exits during an active editing session
function _log_achievements_exit --on-event fish_exit
    # Early exit if logging is disabled or no text editor session was running
    if test -f "$_ACH_RAM_DIR/disabled"; return; end
    if test "$_ACH_EDITOR_ACTIVE" -eq 0; return; end

    mkdir -p $_ACH_RAM_DIR 2>/dev/null

    # Log the abrupt termination with a standard exit code 129 (SIGHUP)
    printf "%s END %s 129\n" (date +%s) "$_CURRENT_RAW_CMD" > $_ACH_LOG_FILE 2>/dev/null
    set -g _ACH_EDITOR_ACTIVE 0
end
