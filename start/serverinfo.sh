#!/usr/bin/env bash
# ============================================================
# serverinfo.sh — красивый отчёт о сервере с цветным выводом
# Совместимость: Linux (bash 4+)
# ============================================================

# ---------- Цвета ----------
if [ -t 1 ]; then
    C_RESET='\033[0m'
    C_BOLD='\033[1m'
    C_DIM='\033[2m'
    C_RED='\033[31m'
    C_GREEN='\033[32m'
    C_YELLOW='\033[33m'
    C_BLUE='\033[34m'
    C_MAGENTA='\033[35m'
    C_CYAN='\033[36m'
    C_BG_BLUE='\033[44m'
    C_BG_GREEN='\033[42m'
else
    C_RESET=''; C_BOLD=''; C_DIM=''; C_RED=''; C_GREEN=''; C_YELLOW=''
    C_BLUE=''; C_MAGENTA=''; C_CYAN=''; C_BG_BLUE=''; C_BG_GREEN=''
fi

bar() {
    local width=50
    local value=$1
    local max=$2
    local filled=0
    [ "$max" -gt 0 ] && filled=$(( value * width / max ))
    local empty=$(( width - filled ))
    local color=$C_GREEN
    [ "$value" -ge 70 ] 2>/dev/null && color=$C_YELLOW
    [ "$value" -ge 90 ] 2>/dev/null && color=$C_RED
    printf '%s%s%s' "$color" "$(printf '#%.0s' $(seq 1 $filled 2>/dev/null) 2>/dev/null || true)" "$C_RESET"
    printf '%s%s' "$C_DIM" "$(printf '-%.0s' $(seq 1 $empty 2>/dev/null) 2>/dev/null || true)" "$C_RESET"
}

section() {
    echo
    printf "${C_BOLD}${C_CYAN}▶ %s${C_RESET}\n" "$1"
    printf "${C_DIM}%s${C_RESET}\n" "------------------------------------------------------------"
}

kv() {
    local key="$1"
    local value="$2"
    local color="${3:-$C_YELLOW}"
    printf "  ${C_BOLD}%-18s${C_RESET} ${color}%s${C_RESET}\n" "$key" "$value"
}

hr() {
    printf "${C_DIM}%s${C_RESET}\n" "════════════════════════════════════════════════════════════"
}

# ---------- Сбор данных ----------
HOSTNAME_S=$(hostname 2>/dev/null || echo "unknown")
OS_S=$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || echo "Unknown OS")
KERNEL_S=$(uname -r)
ARCH_S=$(uname -m)
UPTIME_S=$(uptime -p 2>/dev/null || uptime)
BOOT_S=$(who -b 2>/dev/null | awk '{print $3, $4}' || echo "—")
DATE_S=$(date "+%Y-%m-%d %H:%M:%S %Z")
USERS_S=$(who | wc -l | tr -d ' ')
LOAD_S=$(awk '{print $1, $2, $3}' /proc/loadavg)
PROCS_S=$(ps -e --no-headers 2>/dev/null | wc -l | tr -d ' ')

IP_S=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$IP_S" ] && IP_S=$(ip -4 addr show scope global 2>/dev/null | awk '/inet /{print $2}' | head -1 | cut -d/ -f1)
[ -z "$IP_S" ] && IP_S="—"

# CPU
CPU_MODEL=$(lscpu 2>/dev/null | awk -F: '/Model name/{sub(/^[ \t]+/, "", $2); print $2; exit}')
[ -z "$CPU_MODEL" ] && CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^[ \t]*//')
CPU_CORES=$(nproc 2>/dev/null || echo "—")
CPU_USAGE=$(awk '/^cpu /{usage=($2+$4)*100/($2+$4+$5)} END{printf "%.1f", usage}' /proc/stat 2>/dev/null || echo "0")
CPU_USAGE_INT=${CPU_USAGE%.*}

# RAM
RAM_TOTAL_KB=$(awk '/MemTotal/{print $2}' /proc/meminfo 2>/dev/null)
RAM_AVAIL_KB=$(awk '/MemAvailable/{print $2}' /proc/meminfo 2>/dev/null)
[ -n "$RAM_TOTAL_KB" ] && [ -n "$RAM_AVAIL_KB" ] && \
    RAM_USED_PCT=$(( (RAM_TOTAL_KB - RAM_AVAIL_KB) * 100 / RAM_TOTAL_KB )) || RAM_USED_PCT=0
RAM_TOTAL_H=$(awk -v k="$RAM_TOTAL_KB" 'BEGIN{printf "%.1fG", k/1024/1024}')
RAM_USED_H=$(awk -v k="$RAM_TOTAL_KB" -v a="$RAM_AVAIL_KB" 'BEGIN{printf "%.1fG", (k-a)/1024/1024}')

# Swap
SWAP_TOTAL_KB=$(awk '/SwapTotal/{print $2}' /proc/meminfo 2>/dev/null)
SWAP_FREE_KB=$(awk '/SwapFree/{print $2}' /proc/meminfo 2>/dev/null)
SWAP_USED_PCT=0
[ -n "$SWAP_TOTAL_KB" ] && [ "$SWAP_TOTAL_KB" -gt 0 ] 2>/dev/null && \
    SWAP_USED_PCT=$(( (SWAP_TOTAL_KB - SWAP_FREE_KB) * 100 / SWAP_TOTAL_KB ))

# Диски
DISK_INFO=$(df -h --output=source,size,used,avail,pcent,target 2>/dev/null | tail -n +2)

# Сеть
NET_INFO=$(ip -br addr 2>/dev/null | awk '$2=="UP"{print $1, $3}')

# Топ-5 процессов по памяти
TOP_PROCS=$(ps -eo pid,user,%mem,%cpu,comm --sort=-%mem 2>/dev/null | head -n 6 | awk 'NR==1{print; next} {printf "  %-7s %-10s %5s%% %5s%%  %s\n", $1,$2,$3,$4,$5}')

# ---------- Вывод ----------
clear
printf "${C_BG_BLUE}${C_BOLD}   СЕРВЕР: %-30s   ${C_RESET}\n" "$HOSTNAME_S"
hr

section "🖥️  Система"
kv "Хост"        "$HOSTNAME_S" "$C_GREEN"
kv "ОС"          "$OS_S" "$C_CYAN"
kv "Ядро"        "$KERNEL_S"
kv "Архитектура" "$ARCH_S"
kv "Дата/время"  "$DATE_S" "$C_MAGENTA"
kv "Загрузка"    "$UPTIME_S"
kv "Стартовал"   "$BOOT_S"
kv "Load average" "$LOAD_S" "$C_YELLOW"
kv "Процессов"   "$PROCS_S"
kv "Пользователей" "$USERS_S"

section "⚙️  CPU"
kv "Модель"      "$CPU_MODEL" "$C_CYAN"
kv "Ядер"        "$CPU_CORES"
printf "  ${C_BOLD}%-18s${C_RESET} %s%s%%%s  " "Загрузка" "$C_YELLOW" "$CPU_USAGE" "$C_RESET"
bar "$CPU_USAGE_INT" 100
echo

section "💾  Память"
kv "Всего"       "$RAM_TOTAL_H"
kv "Использовано" "$RAM_USED_H"
printf "  ${C_BOLD}%-18s${C_RESET} %s%s%%%s  " "RAM" "$C_YELLOW" "$RAM_USED_PCT" "$C_RESET"
bar "$RAM_USED_PCT" 100
echo
kv "Swap всего"  "$(awk -v k="$SWAP_TOTAL_KB" 'BEGIN{printf "%.1fG", k/1024/1024}')"
printf "  ${C_BOLD}%-18s${C_RESET} %s%s%%%s  " "Swap" "$C_YELLOW" "$SWAP_USED_PCT" "$C_RESET"
bar "$SWAP_USED_PCT" 100
echo

section "📀  Диски"
if [ -n "$DISK_INFO" ]; then
    printf "  ${C_BOLD}%-22s %-6s %-6s %-6s %-5s %s${C_RESET}\n" "Устройство" "Размер" "Исп." "Своб." "%%" "Точка"
    echo "$DISK_INFO" | while read -r line; do
        fs=$(echo "$line" | awk '{print $1}')
        sz=$(echo "$line" | awk '{print $2}')
        us=$(echo "$line" | awk '{print $3}')
        av=$(echo "$line" | awk '{print $4}')
        pc=$(echo "$line" | awk '{print $5}' | tr -d '%')
        tg=$(echo "$line" | awk '{print $6}')
        color=$C_GREEN
        [ "$pc" -ge 70 ] 2>/dev/null && color=$C_YELLOW
        [ "$pc" -ge 90 ] 2>/dev/null && color=$C_RED
        printf "  %-22s %-6s %-6s %-6s ${color}%-5s${C_RESET} %s\n" "$fs" "$sz" "$us" "$av" "${pc}%" "$tg"
        printf "    "; bar "$pc" 100; echo
    done
else
    echo "  (не удалось получить информацию)"
fi

section "🌐  Сеть"
kv "IP-адрес"    "$IP_S" "$C_GREEN"
if [ -n "$NET_INFO" ]; then
    echo "$NET_INFO" | while read -r iface addr; do
        kv "  $iface" "$addr" "$C_CYAN"
    done
fi

section "🔥  Топ процессов (по памяти)"
printf "${C_DIM}  %-7s %-10s %6s %6s  %s${C_RESET}\n" "PID" "USER" "MEM%" "CPU%" "COMMAND"
echo "$TOP_PROCS"

hr
printf "${C_DIM}  сгенерировано: %s${C_RESET}\n" "$(date '+%Y-%m-%d %H:%M:%S')"
echo
