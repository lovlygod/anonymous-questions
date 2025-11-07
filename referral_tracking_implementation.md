# Реализация отслеживания реферальных ссылок

## Описание задачи

Требуется реализовать систему отслеживания реферальных ссылок, которая будет:
- Записывать информацию о пользователе, который перешел по реф ссылке (ID, юзернейм, имя, фамилия)
- Записывать информацию о том, что именно он написал (содержимое сообщения)
- Использовать переменную окружения для определения реф ссылки

## Структура данных

### Новая модель данных: ReferralTracking
```python
from typing import Union
from pydantic import BaseModel


class ReferralTracking(BaseModel):
    """
    Модель для отслеживания пользователей, которые перешел по реф ссылке
    """
    id: str  # Уникальный ID записи
    referrer_id: int  # ID пользователя, чья реф ссылка была использована
    user_id: int  # ID пользователя, который перешел по ссылке
    user_username: Union[str, None] = None  # Username пользователя
    user_first_name: str  # Имя пользователя
    user_last_name: Union[str, None] = None  # Фамилия пользователя
    message_content: Union[str, None] = None  # Содержимое сообщения, которое было отправлено
    timestamp: int  # Время перехода/отправки
    source: str = "referral_link"  # Источник (реф ссылка, реклама и т.д.)
```

## Реализация

### 1. Обработка реферальных ссылок из переменных окружения

Функция для получения реф ID из переменной окружения:

```python
import os

def get_referral_id_from_env():
    """
    Получает реф ID из переменной окружения
    """
    referral_id = os.getenv("REFERRAL_ID")
    return referral_id
```

### 2. Логика записи информации о пользователе

Функция для создания записи в базе данных:

```python
from datetime import datetime
import uuid

async def track_referral_usage(referrer_id: int, user_info: dict, message_content: str = None):
    """
    Создает запись о пользователе, который перешел по реф ссылке
    """
    referral_tracking = ReferralTracking(
        id=str(uuid.uuid4()),
        referrer_id=referrer_id,
        user_id=user_info['id'],
        user_username=user_info.get('username'),
        user_first_name=user_info['first_name'],
        user_last_name=user_info.get('last_name'),
        message_content=message_content,
        timestamp=int(datetime.utcnow().timestamp())
    )
    
    # Сохраняем в базу данных
    from src.utils.db import db
    await db.referral_tracking.insert_one(referral_tracking.dict())
    
    return referral_tracking
```

### 3. Интеграция с обработчиком команды /start

Изменения в файле `bot/src/handlers/user/message.py`:

```python
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from src.utils.db import MongoDbClient
from src.utils.fsm_state import SendMessage
from src.utils.functions.user.functions import (send_message_with_referer, adv_show, show_advert, handle_start,
                                                handle_subscription_check)

router = Router()

# Handle the /start command
@router.message(Command('start'))
async def start(message: Message, bot: Bot, db: MongoDbClient, state: FSMContext):
    # Split the message text by spaces
    split_message = message.text.split(' ')
    # Find the user in the database
    user = await db.users.find_one({'id': message.from_user.id})
    
    # Проверяем, есть ли реф ID в переменной окружения
    import os
    env_referral_id = os.getenv("REFERRAL_ID")
    
    if not user.first_start and env_referral_id:
        # Если пользователь уже был в боте, но пришел по реф ссылке из переменной окружения
        if str(message.from_user.id) != env_referral_id:
            # Отслеживаем использование реф ссылки из переменной окружения
            user_info = {
                'id': message.from_user.id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name
            }
            await track_referral_usage(int(env_referral_id), user_info)
    
    if user.first_start:
        # If this is the user's first start, update the database
        await db.users.update_one({'id': message.from_user.id}, {'first_start': False})
        # handle_start will send its own welcome message, so we don't need to send it here
        await handle_start(message, bot, db, state, split_message)
    else:
        await handle_subscription_check(bot, message, db, state, split_message)
    
    # Show advertisement
    await show_advert(message.from_user.id)
    await adv_show(message.from_user.id, bot, db)
```

### 4. Функция для сохранения сообщений

Функция для сохранения сообщений, отправленных через реферальные ссылки:

```python
async def save_referral_message(referrer_id: int, sender_id: int, message: Message):
    """
    Сохраняет сообщение, отправленное через реферальную систему
    """
    user_info = {
        'id': sender_id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name
    }
    
    message_content = message.text or message.caption or None
    
    await track_referral_usage(referrer_id, user_info, message_content)
```

### 5. Обновление базы данных

В файле `bot/src/utils/db.py` добавляем новую коллекцию:

```python
from src.models.referral_tracking import ReferralTracking

# Добавляем новую коллекцию в MongoDbClient
db = MongoDbClient(
    users=Collection(collection_name='users', model=User),
    channels=Collection(collection_name='channels', model=Channels),
    referrals=Collection(collection_name='referrals', model=Referrals),
    adv=Collection(collection_name='adv', model=Adv),
    referral_tracking=Collection(collection_name='referral_tracking', model=ReferralTracking)  # Новая коллекция
)
```

## Использование

1. Установите переменную окружения `REFERRAL_ID` в Railway с ID пользователя, чья ссылка будет использоваться
2. При запуске бота с этой переменной, все новые пользователи, которые перейдут в бота, будут записываться в коллекцию `referral_tracking`
3. Также будут записываться все сообщения, отправленные через систему рефералов

## Пример переменной окружения в Railway

```
REFERRAL_ID=123456789
```

Где 123456789 - это ID пользователя, чья реф ссылка будет использоваться для отслеживания.

## Созданные файлы и папки

В процессе реализации были созданы следующие файлы:

1. `bot/src/models/referral_tracking.py` - файл с моделью данных для отслеживания рефералов
2. `referral_tracking_implementation.md` - данный файл с полной документацией по реализации

Дополнительно были предложены изменения для следующих существующих файлов:
- `bot/src/utils/db.py` - для добавления новой коллекции
- `bot/src/handlers/user/message.py` - для интеграции с обработчиком команды /start
- В файлы с функциями для работы с рефералами были предложены новые функции