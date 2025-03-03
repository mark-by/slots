#!/bin/sh
set -e

# Применяем миграции
python manage.py migrate --noinput

# Если нужно, можно собрать статические файлы (опционально)
# python manage.py collectstatic --noinput

# Выполняем команду, переданную в CMD
exec "$@"
