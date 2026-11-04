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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# ==============================================================================
# WARNING & SECURITY NOTICE:
# - This script logs the last terminal command
# - Use strictly at your own risk. The author assumes no liability for leaks.
#==============================================================================


# Загружаем встроенный модуль работы со временем (работает в памяти Zsh)
zmodload zsh/datetime 2>/dev/null

# Флаг состояния (0 - свободен, 1 - редактор запущен)
_ACH_EDITOR_ACTIVE=0

# Путь к изолированной RAM текущего пользователя
_ACH_RAM_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/linux-achievements"
_ACH_LOG_FILE="$_ACH_RAM_DIR/last_cmd"

# Регулярка под PCRE (Zsh), учитывает sudo, флаги sudo и пути
_ACH_ED_REGEX='^([[:space:]]*sudo([[:space:]]+-[a-zA-Z0-9]+([[:space:]]+[^[:space:]]+)?)?[[:space:]]+)?([^[:space:]]*/)?(vi|vim|nvim|nano|emacs|mcedit|gedit|kate|micro|visudo|sudoedit)([[:space:]]|$)'

# Инициализация дефолтного редактора
if mkdir -p "$_ACH_RAM_DIR" 2>/dev/null; then
    _ed="${EDITOR:-nano}"
    _ed="${_ed%% *}"
    _ed="${_ed##*/}"
    printf "%s\n" "$_ed" > "$_ACH_RAM_DIR/editor" 2>/dev/null
fi

# Функция 1: Срабатывает СТРОГО ДО запуска команды (START)
_log_achievements_preexec() {
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return
    (( _ACH_EDITOR_ACTIVE == 1 )) && return

    local current_cmd="$1"
    [[ -z "$current_cmd" || "$current_cmd" == *"_log_achievements"* ]] && return

    zmodload zsh/pcre 2>/dev/null

    if [[ "$current_cmd" =~ $_ACH_ED_REGEX ]]; then
        _ACH_EDITOR_ACTIVE=1
        _CURRENT_RAW_CMD="$current_cmd"
        mkdir -p "$_ACH_RAM_DIR" 2>/dev/null
        # ИСПОЛЬЗУЕМ $EPOCHSECONDS — работает мгновенно без вызова /bin/date
        printf "%s START %s\n" "$EPOCHSECONDS" "$current_cmd" > "$_ACH_LOG_FILE" 2>/dev/null
    fi
}

# Функция 2: Срабатывает ПОСЛЕ завершения команды (END)
_log_achievements_precmd() {
    local exit_code=$?
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return

    # Достаем последнюю команду из истории Zsh (флаг -n убирает номера)
    local last_cmd
    last_cmd=$(fc -ln -1 -1 2>/dev/null)
    last_cmd=$(echo "$last_cmd" | xargs)

    [[ -z "$last_cmd" || "$last_cmd" == *"_log_achievements"* ]] && return

    _ACH_EDITOR_ACTIVE=0

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null
    # ИСПОЛЬЗУЕМ $EPOCHSECONDS — работает мгновенно без вызова /bin/date
    printf "%s END %s %s\n" "$EPOCHSECONDS" "$last_cmd" "$exit_code" > "$_ACH_LOG_FILE" 2>/dev/null
}

# Функция 3: Ловушка на закрытие терминала крестиком
_log_achievements_zsh_exit() {
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return
    (( _ACH_EDITOR_ACTIVE == 0 )) && return

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null
    printf "%s END %s 129\n" "$EPOCHSECONDS" "$_CURRENT_RAW_CMD" > "$_ACH_LOG_FILE" 2>/dev/null
    _ACH_EDITOR_ACTIVE=0
}

# Регистрируем функции в стандартные хуки Zsh
autoload -Uz add-zsh-hook
add-zsh-hook preexec _log_achievements_preexec
add-zsh-hook precmd _log_achievements_precmd

# Ловушка выхода
trap '_log_achievements_zsh_exit' EXIT
