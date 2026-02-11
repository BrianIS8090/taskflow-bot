#!/bin/bash
# Запуск TaskFlow Scheduler Bot

cd /root/.openclaw/workspace/taskflow-bot

# Активируем окружение
source /root/.openclaw/workspace/hh-analyzer/venv/bin/activate

# Проверяем токен
if grep -q 'BOT_TOKEN = os.getenv("TASKFLOW_BOT_TOKEN", "")' config.py; then
    echo "❌ Ошибка: Токен бота не установлен!"
    echo ""
    echo "Для получения токена:"
    echo "1. Откройте @BotFather в Telegram"
    echo "2. Отправьте /newbot"
    echo "3. Придумайте имя: TaskFlow Scheduler Bot"
    echo "4. Придумайте username: taskflow_scheduler_bot"
    echo "5. Скопируйте токен"
    echo ""
    echo "Затем обновите config.py:"
    echo "BOT_TOKEN = 'ВАШ_ТОКЕН'"
    exit 1
fi

# Запускаем бота
echo "🚀 Запуск TaskFlow Scheduler Bot..."
nohup python bot.py > bot.log 2>&1 &

sleep 2

if pgrep -f "taskflow-bot/bot.py" > /dev/null; then
    echo "✅ Бот успешно запущен!"
    echo "📋 Логи: /root/.openclaw/workspace/taskflow-bot/bot.log"
else
    echo "❌ Ошибка запуска. Проверьте логи:"
    cat bot.log
fi
