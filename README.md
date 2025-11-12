# Anonymous Questions Bot

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Telegram](https://img.shields.io/badge/telegram-bot-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Описание

**Anonymous Questions Bot** - это Telegram бот, позволяющий пользователям получать анонимные вопросы от других пользователей через уникальные ссылки. Бот предоставляет удобную админ-панель для управления и мониторинга активности.

## Особенности

- **Анонимные вопросы**: Пользователи могут задавать вопросы анонимно, без раскрытия своей личности
- **Уникальные ссылки**: Каждый пользователь получает уникальную ссылку для получения вопросов
- **Админ-панель**: Расширенные возможности управления ботом
- **Поддержка медиа**: Возможность отправки ответов в различных форматах (текст, фото, видео и др.)
- **Статистика**: Подробная аналитика использования бота
- **Рассылка**: Возможность отправки сообщений всем пользователям
- **Реферальная система**: Автогенерация реферальных ссылок для привлечения пользователей
- **Рекламные посты**: Поддержка показа рекламных материалов
- **Каналы подписки**: Возможность требовать подписку на каналы для использования бота

## Технологии

- **Python 3.8+**: Основной язык программирования
- **Aiogram**: Асинхронный фреймворк для Telegram Bot API
- **MongoDB**: База данных для хранения информации о пользователях и вопросах
- **Redis**: Кэширование и хранение временных данных
- **Docker**: Контейнеризация приложения
- **PyMongo**: Драйвер для работы с MongoDB
- **Environs**: Управление переменными окружения

## Установка и запуск

### Локальный запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/lovlygod/anonymous-questions.git
cd anonymous-questions
```

2. Установите зависимости:
```bash
pip install -r bot/requirements.txt
```

3. Создайте файл `.env` на основе `.env.example` и настройте переменные окружения:
```env
API_TOKEN=ваш_токен_телеграм_бота
MONGO_URI=mongodb://localhost:27017/anonymous_questions
REDIS_HOST=localhost
REDIS_PORT=6379
ADMIN_ID=ваш_телеграм_id
```

4. Запустите бота:
```bash
python bot/main.py
```

### Запуск с Docker

1. Соберите образ:
```bash
docker build -t anonymous-questions-bot .
```

2. Запустите контейнер:
```bash
docker run -d --env-file .env anonymous-questions-bot
```

### Запуск с Docker Compose

1. Запустите сервисы:
```bash
docker-compose up -d
```

## Структура проекта

```
anonymous-questions/
├── bot/
│   ├── main.py                 # Основной файл запуска бота
│   ├── config.py              # Конфигурация приложения
│   ├── requirements.txt       # Зависимости
│   └── src/
│       ├── handlers/          # Обработчики команд и сообщений
│       │   ├── admin/         # Обработчики админ-панели
│       │   └── user/          # Обработчики пользовательской части
│       ├── models/            # Модели данных
│       ├── utils/             # Вспомогательные функции
│       │   ├── functions/     # Функции для работы с данными
│       │   └── middlewares/   # Промежуточные обработчики
│       └── callbacks.py       # Обработчики callback-запросов
├── docker-compose.yml         # Конфигурация Docker Compose
├── Dockerfile                # Docker-файл для основного сервиса
├── dockerfile.bot            # Альтернативный Docker-файл
├── .env.example              # Пример файла переменных окружения
├── .gitignore                # Файлы, игнорируемые Git
└── README.md                 # Документация
```

## Функциональность

### Для пользователей:
- Получение уникальной ссылки для анонимных вопросов
- Ответы на вопросы в различных форматах
- Возможность управления своими вопросами

### Для администраторов:
- Просмотр статистики пользователей и активности
- Выгрузка данных пользователей
- Рассылка сообщений
- Управление каналами подписки
- Управление реферальной системой
- Добавление и редактирование рекламных постов

## Переменные окружения

- `API_TOKEN` - Токен Telegram бота
- `MONGO_URI` - Строка подключения к MongoDB
- `REDIS_HOST` - Хост Redis (по умолчанию localhost)
- `REDIS_PORT` - Порт Redis (по умолчанию 6379)
- `ADMIN_ID` - ID администратора бота
- `DATABASE_NAME` - Имя базы данных (по умолчанию anonymous_questions)

## Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для вашей фичи: `git checkout -b feature/AmazingFeature`
3. Зафиксируйте изменения: `git commit -m 'Add some AmazingFeature'`
4. Отправьте ветку: `git push origin feature/AmazingFeature`
5. Создайте Pull Request

## Лицензия

Distributed under the MIT License. See `LICENSE` for more information.

## Контакты

- Проект: [https://github.com/lovlygod/anonymous-questions](https://github.com/lovlygod/anonymous-questions)
- Автор: lovlygod
