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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# ==============================================================================
# WARNING & SECURITY NOTICE:
# - This script logs the last terminal command
# - Use strictly at your own risk. The author assumes no liability for leaks.
#==============================================================================

# Флаг состояния (0 - свободен, 1 - редактор запущен)
_ACH_EDITOR_ACTIVE=0

# Путь к изолированной RAM текущего пользователя
_ACH_RAM_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/linux-achievements"
_ACH_LOG_FILE="$_ACH_RAM_DIR/last_cmd"

# Регулярка для быстрой проверки редакторов (учитывает sudo, флаги sudo и пути)
_ACH_ED_REGEX='^([[:space:]]*sudo([[:space:]]+-[a-zA-Z0-9]+([[:space:]]+[^[:space:]]+)?)?[[:space:]]+)?([^[:space:]]*/)?(vi|vim|nvim|nano|emacs|mcedit|gedit|kate|micro|visudo|sudoedit)([[:space:]]|$)'

# Инициализация RAM-директории и определение дефолтного редактора
if mkdir -p "$_ACH_RAM_DIR" 2>/dev/null; then
    _ed="${EDITOR:-nano}"
    _ed="${_ed%% *}"
    _ed="${_ed##*/}"
    printf "%s\n" "$_ed" > "$_ACH_RAM_DIR/editor" 2>/dev/null
fi

# Функция 1: Срабатывает ДО запуска команды (Фиксируем СТАРТ только для редакторов)
_log_achievements_start() {
    # ПРОВЕРКА БЛОКИРОВКИ: если запись выключена утилитой, выходим
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return

    [[ -z "$BASH_COMMAND" || "$BASH_COMMAND" == "$PROMPT_COMMAND" ]] && return
    [[ "$BASH_COMMAND" == *"_log_achievements"* || "$BASH_COMMAND" == *"__vte"* ]] && return
    (( _ACH_EDITOR_ACTIVE == 1 )) && return

    # Проверяем команду нашей быстрой регуляркой прямо в памяти Bash
    if [[ "$BASH_COMMAND" =~ $_ACH_ED_REGEX ]]; then
        _ACH_EDITOR_ACTIVE=1
        _CURRENT_RAW_CMD="$BASH_COMMAND"
        mkdir -p "$_ACH_RAM_DIR" 2>/dev/null

        # ЧИСТЫЙ СТАРТ: Только таймстамп, статус и сама команда
        printf "%(%s)T START %s\n" "-1" "$BASH_COMMAND" > "$_ACH_LOG_FILE" 2>/dev/null
    fi
}

# Функция 2: Срабатывает ПОСЛЕ завершения команды (Фиксируем ИСХОД для всего)
_log_achievements_bash() {
    local exit_code=$?

    # ПРОВЕРКА БЛОКИРОВКИ: если запись выключена утилитой, выходим
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return

    [[ "$BASH_COMMAND" == "$PROMPT_COMMAND" ]] && return

    # Вытаскиваем из буфера текущую активную строку истории через встроенный макрос
    local last_cmd
    last_cmd=$(history 1)

    # Очищаем от номеров строк истории, которые Bash успел приписать
    last_cmd="${last_cmd#*[0-9]*  }"
    # Убираем лишние пробелы по краям
    last_cmd=$(echo "$last_cmd" | xargs)

    [[ -z "$last_cmd" || "$last_cmd" == *"_log_achievements"* || "$last_cmd" == *"__vte"* ]] && return

    _ACH_EDITOR_ACTIVE=0

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null
    # Записываем: ТАЙМСТАМП END ОРИГИНАЛЬНАЯ_КОМАНДА КОД_ВОЗВРАТА
    printf "%(%s)T END %s %s\n" "-1" "$last_cmd" "$exit_code" > "$_ACH_LOG_FILE" 2>/dev/null
}

# Функция 3: Срабатывает, если терминал закрыли крестиком во время работы редактора
_log_achievements_exit() {
    trap - DEBUG

    # ПРОВЕРКА БЛОКИРОВКИ: если запись выключена утилитой, выходим
    [[ -f "$_ACH_RAM_DIR/disabled" ]] && return
    (( _ACH_EDITOR_ACTIVE == 0 )) && return

    mkdir -p "$_ACH_RAM_DIR" 2>/dev/null
    # Записываем END для оборванного редактора с кодом 129
    printf "%(%s)T END %s 129\n" "-1" "$_CURRENT_RAW_CMD" > "$_ACH_LOG_FILE" 2>/dev/null
    _ACH_EDITOR_ACTIVE=0
}

set +t

if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="_log_achievements_bash"
elif [[ "$PROMPT_COMMAND" != *"_log_achievements_bash"* ]]; then
    PROMPT_COMMAND="_log_achievements_bash; $PROMPT_COMMAND"
fi

trap '_log_achievements_start' DEBUG
trap '_log_achievements_exit' EXIT
