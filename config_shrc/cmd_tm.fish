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

# Флаг состояния
set -g _ACH_EDITOR_ACTIVE 0

# Пути к RAM
set -g _ACH_RAM_DIR (string join '/' (or $XDG_RUNTIME_DIR "/run/user/"(id -u)) "linux-achievements")
set -g _ACH_LOG_FILE "$_ACH_RAM_DIR/last_cmd"

# Список редакторов для проверки
set -g _ACH_EDITORS vi vim nvim nano emacs mcedit gedit kate micro visudo sudoedit

# Инициализация дефолтного редактора
if mkdir -p $_ACH_RAM_DIR 2>/dev/null
    set -l _ed (or $EDITOR "nano")
    set _ed (string split ' ' $_ed)
    set _ed (basename $_ed[1])
    echo $_ed > "$_ACH_RAM_DIR/editor"
end

# Оптимизированный хелпер для быстрого поиска бинарника
function _ach_get_binary
    set -l cmd_args (string split ' ' (string trim $argv))
    set -l idx 1
    while test $idx -le (count $cmd_args)
        if test "$cmd_args[$idx]" = "sudo"
            set idx (math $idx + 1)
            while test $idx -le (count $cmd_args); and string match -r '^-' "$cmd_args[$idx]"
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

# Функция 1: Срабатывает ДО выполнения команды (START)
function _log_achievements_start --on-event fish_preexec
    if test -f "$_ACH_RAM_DIR/disabled"; return; end
    if test "$_ACH_EDITOR_ACTIVE" -eq 1; return; end
    if string match -q "*_log_achievements*" "$argv"; return; end

    set -l clean_bin (_ach_get_binary "$argv")

    if contains "$clean_bin" $_ACH_EDITORS
        set -g _ACH_EDITOR_ACTIVE 1
        set -g _CURRENT_RAW_CMD "$argv"
        mkdir -p $_ACH_RAM_DIR 2>/dev/null
        # Запись происходит мгновенно
        printf "%s START %s\n" (date +%s) "$argv" > $_ACH_LOG_FILE 2>/dev/null
    fi
end

# Функция 2: Срабатывает ПОСЛЕ выполнения команды (END)
function _log_achievements_bash --on-event fish_postexec
    set -l exit_code $status
    if test -f "$_ACH_RAM_DIR/disabled"; return; end
    if string match -q "*_log_achievements*" "$argv"; return; end

    set -g _ACH_EDITOR_ACTIVE 0
    mkdir -p $_ACH_RAM_DIR 2>/dev/null
    set -l last_cmd (string trim "$argv")

    printf "%s END %s %s\n" (date +%s) "$last_cmd" $exit_code > $_ACH_LOG_FILE 2>/dev/null
end

# Функция 3: Срабатывает при закрытии терминала
function _log_achievements_exit --on-event fish_exit
    if test -f "$_ACH_RAM_DIR/disabled"; return; end
    if test "$_ACH_EDITOR_ACTIVE" -eq 0; return; end

    mkdir -p $_ACH_RAM_DIR 2>/dev/null
    printf "%s END %s 129\n" (date +%s) "$_CURRENT_RAW_CMD" > $_ACH_LOG_FILE 2>/dev/null
    set -g _ACH_EDITOR_ACTIVE 0
end
