# M3U_fastapi
API приложения для просмотра плейлистов в формате M3U.
#
### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/abp-ce/m3u_fastapi.git
```

```
cd m3u_fastapi.git
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

```
python3 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
alembic upgrade head
```

Запустить проект:

```
uvicorn main:app --reload
```
### Стек:
 - fastapi 0.68.1
 - SQLAlchemy 1.4.27
 - alembic 1.8.0
 - cx-Oracle 8.2.1