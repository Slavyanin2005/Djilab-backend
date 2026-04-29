# DJILab Backend

Серверная часть платформы для продажи лабораторного оборудования. Построена на **Django** + **Django REST Framework** с использованием **PostgreSQL** и **MinIO**.

---

## Содержание

- [Описание](#описание)
- [Структура проекта](#структура-проекта)
- [Технологии](#технологии)
- [Установка и запуск](#установка-и-запуск)
- [Переменные окружения](#переменные-окружения)
- [API Документация](#api-документация)
- [Code Style](#code-style)
- [Docker](#docker)
- [Pre-commit хуки](#pre-commit-хуки)

---

## Описание

Backend предоставляет:
- **REST API** для взаимодействия с фронтендом (React + TypeScript)
- **HTML-шаблоны** для серверного рендеринга (Django Templates)
- **Админ-панель** для управления товарами, заказами и пользователями
- **Интеграцию с MinIO** для хранения изображений товаров
- **Систему заказов** со статусами (черновик, сформирован, завершён, отклонён)

---

## Структура проекта

```
backend/
├── catalog/                    # Приложение каталога и заказов
│   ├── migrations/             # Миграции БД
│   ├── admin.py                # Админ-панель
│   ├── api_urls.py             # API URL маршруты
│   ├── api_views.py            # API ViewSets
│   ├── models.py               # Модели данных
│   ├── serializers.py          # DRF сериализаторы
│   ├── urls.py                 # HTML URL маршруты
│   └── views.py                # HTML views
├── djilab/                     # Основной проект Django
│   ├── settings.py             # Настройки проекта
│   ├── urls.py                 # Корневые URL
│   ├── wsgi.py                 # WSGI конфигурация
├── static/                     # Статические файлы
│   └── styles.css              # Основные стили
├── templates/                  # HTML шаблоны
│   ├── index.html              # Главная страница (каталог)
│   ├── product.html            # Страница товара
│   ├── cart.html               # Корзина
│   └── orders_history.html     # История заказов
├── venv/                       # Виртуальное окружение
├── .env                        # Переменные окружения
├── .env.example                # Пример переменных окружения
├── Dockerfile                  # Docker образ
├── manage.py                   # Django manage script
├── pyproject.toml              # Настройки black и isort
├── requirements.txt            # Python зависимости
└── README.md                   # Описание проекта
```

---

## Технологии

| Технология | Версия | Назначение | Документация |
|------------|--------|------------|--------------|
| **Python** | 3.11 | Язык программирования | [docs.python.org](https://docs.python.org/3/) |
| **Django** | 5.2.11 | Web-фреймворк | [docs.djangoproject.com](https://docs.djangoproject.com/) |
| **Django REST Framework** | 3.15.2 | REST API | [django-rest-framework.org](https://www.django-rest-framework.org/) |
| **PostgreSQL** | 15 | База данных | [postgresql.org/docs](https://www.postgresql.org/docs/) |
| **MinIO** | latest | Объектное хранилище | [min.io/docs](https://min.io/docs/) |
| **psycopg** | 3.3.3 | PostgreSQL драйвер | [psycopg.org/docs](https://www.psycopg.org/docs/) |
| **black** | 24.4.2 | Форматтер кода | [black.readthedocs.io](https://black.readthedocs.io/) |
| **isort** | 5.13.2 | Сортировка импортов | [pycqa.github.io/isort](https://pycqa.github.io/isort/) |
| **flake8** | 7.1.0 | Линтер | [flake8.pycqa.org](https://flake8.pycqa.org/) |
| **pre-commit** | 3.7.1 | Pre-commit хуки | [pre-commit.com](https://pre-commit.com/) |
| **django-cors-headers** | 4.3.1 | CORS для React | [github.com/adamchainz/django-cors-headers](https://github.com/adamchainz/django-cors-headers) |

---

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/Slavyanin2005/DJILAB-project.git
cd DJILAB-project/backend
```

### 2. Создание виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

```bash
# Скопируйте пример
copy .env.example .env

# Отредактируйте .env под вашу конфигурацию
```

### 5. Применение миграций

```bash
python manage.py migrate
```

### 6. Создание суперпользователя

```bash
python manage.py createsuperuser
```

### 7. Запуск сервера

```bash
python manage.py runserver
```

**Сервер доступен по адресу:** http://localhost:8000/

---

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| `DEBUG` | Режим отладки | `True` / `False` |
| `SECRET_KEY` | Секретный ключ Django | `django-insecure-...` |
| `DB_NAME` | Имя базы данных | `djilab_db` |
| `DB_USER` | Пользователь БД | `admin` |
| `DB_PASSWORD` | Пароль БД | `your-password` |
| `DB_HOST` | Хост БД | `localhost` / `postgres` |
| `DB_PORT` | Порт БД | `5432` / `5433` |
| `MINIO_URL` | URL MinIO | `http://localhost:9000` |
| `MINIO_BUCKET` | Имя бакета | `djilab-products` |
| `MINIO_ACCESS_KEY` | Ключ доступа MinIO | `admin` |
| `MINIO_SECRET_KEY` | Секретный ключ MinIO | `your-secret-key` |

---

## API Документация

### Базовый URL

```
http://localhost:8000/api/
```

### Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/api/services/` | Список всех услуг |
| `GET` | `/api/services/{id}/` | Детальная информация об услуге |
| `POST` | `/api/services/{id}/add_to_order/` | Добавить услугу в заказ |
| `GET` | `/api/orders/` | Список всех заказов |
| `GET` | `/api/orders/{id}/` | Детальная информация о заказе |
| `POST` | `/api/orders/` | Создать новый заказ |
| `POST` | `/api/orders/{id}/add_item/` | Добавить позицию в заказ |
| `POST` | `/api/orders/{id}/update_item/` | Обновить позицию в заказе |
| `POST` | `/api/orders/{id}/remove_item/` | Удалить позицию из заказа |
| `POST` | `/api/orders/{id}/submit/` | Отправить заказ |
| `POST` | `/api/orders/{id}/delete/` | Удалить заказ |
| `GET` | `/api/profiles/` | Профиль пользователя |

### Пример запроса

```bash
# Получить список услуг
curl http://localhost:8000/api/services/

# Создать заказ
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d "{}"
```

### Пример ответа

```json
{
  "id": 1,
  "status": "draft",
  "status_display": "Черновик",
  "creator": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  },
  "created_at": "2026-03-09T10:00:00Z",
  "total": "1000.00",
  "items_count": 1,
  "items": [
    {
      "id": 1,
      "service": {
        "id": 1,
        "name": "pH-метр",
        "price": "1000.00"
      },
      "quantity": 1,
      "subtotal": "1000.00"
    }
  ]
}
```

---

## Code Style

### Именование

| Тип | Стиль | Пример |
|-----|-------|--------|
| Переменные | `snake_case` | `user_id`, `order_total` |
| Функции | `snake_case` | `get_order()`, `create_service()` |
| Классы | `PascalCase` | `OrderItem`, `UserProfile` |
| Файлы | `snake_case.py` | `api_views.py`, `serializers.py` |
| Константы | `UPPER_SNAKE_CASE` | `DEBUG`, `SECRET_KEY` |

### Инструменты

| Инструмент | Назначение | Команда |
|------------|------------|---------|
| **Black** | Автоматическое форматирование | `black .` |
| **isort** | Сортировка импортов | `isort .` |
| **flake8** | Линтинг (поиск ошибок) | `flake8 .` |

### Конфигурация

**pyproject.toml:**
```toml
[tool.black]
line-length = 120
target-version = ['py311']
exclude = '''
/(
    \.git
  | __pycache__
  | venv
  | migrations
  | static
  | media
)/
'''

[tool.isort]
profile = "black"
line_length = 120
skip = ["venv", "migrations", "static", "media"]
```

**.flake8:**
```ini
[flake8]
max-line-length = 120
exclude =
    .git,
    __pycache__,
    venv,
    migrations,
    static,
    media,
    *.pyc
ignore = E203, W503, E501, F401
```

---

## Docker

### Сборка и запуск

```bash
# Сборка образа
docker-compose build backend

# Запуск контейнера
docker-compose up -d backend

# Просмотр логов
docker-compose logs backend
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## Pre-commit хуки

### Установка

```bash
# Активировать виртуальное окружение
venv\Scripts\activate

# Установить pre-commit
pip install pre-commit

# Инициализировать хуки
pre-commit install
```

### Доступные хуки

| Хук | Описание |
|-----|----------|
| `trailing-whitespace` | Удаляет пробелы в конце строк |
| `end-of-file-fixer` | Добавляет пустую строку в конец файла |
| `check-yaml` | Проверяет валидность YAML файлов |
| `check-added-large-files` | Проверка размера файлов (< 1MB) |
| `check-merge-conflict` | Проверка конфликтов слияния |
| `black` | Форматирование Python кода |
| `isort` | Сортировка импортов |
| `flake8` | Линтинг Python кода |

### Запуск вручную

```bash
# Проверить все файлы
pre-commit run --all-files

# Проверить только изменённые файлы
pre-commit run
```

---

## Контакты

- **Email**: ostafinskijvadim@gmail.com
- **Телефон**: +7 (905) 978-65-14
- **Адрес репозитория**: https://github.com/Slavyanin2005/DJILAB-project

---

## Лицензия

Проект создан в учебных целях для курсовой работы.
