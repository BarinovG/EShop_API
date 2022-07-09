# Запуск
## Cоздать виртуальное окружение
-- python -m venv *name_venv*

## Активировать его
для Windows:
-- *name_venv*/Scripts/activate

для Linux/MacOS:
-- source *name_venv*/bin/activate

## Обновим pip
-- python -m pip install --upgrade pip

## Установим зависимости
-- pip install -r requirements.txt

## Редактирование настроек
Добавить в виртуальное окружение переменные:
SECRET_KEY, DEBUG, db_name, db_user, db_pass, host_mail, host_pass

## Запустить сервер Django
python manage.py makemigrations

python manage.py migrate

python manage.py runserver

## Запустить сервер Redis
redis-server

## Запустить Celery
celery -A EShops_API  worker -l info -P gevent


