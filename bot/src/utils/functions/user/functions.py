import os
import re
import traceback
import uuid
from datetime import datetime
import time

import aiohttp
import logging
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.callbacks import Reply, SendAgain, GetLink, Start
from src.utils.fsm_state import SendMessage
from src.utils.photo import send_message_photo, new_message, answer_sended, welcome
from src.utils.text import hello_referer
from src.models.referral_tracking import ReferralTracking
from src.utils.logger import perf_logger

log = logging.getLogger('adverts')


# Function to sort actions and send messages with referer
async def send_message_with_referer(message, bot, state, data: dict, referer: int, sender: int):
    message_id = data.get('message_id')
    if message_id:
        try:
            # Attempt to delete the message
            await bot.delete_message(chat_id=message.from_user.id, message_id=int(message_id))
        except Exception:
            pass
    action = data.get('action')
    if action == 'reply':
        await reply_action(message, bot, state, data, referer, sender)
    elif action == 'send':
        await send_action(message, bot, state, data, referer)


# Function to handle start with or without a referral link
async def handle_start(message, bot, db, state, split_message):
    # Get the referral link if it exists
    ref = split_message[1] if len(split_message) > 1 else None
    # Find the referral link in the database
    ref_link = await db.referrals.find_one({'id': ref}) if ref else None
    if ref_link:
        # Update the number of clicks on the referral link
        await db.referrals.update_one({'id': ref}, {'clicks': int(ref_link.clicks) + 1})
        # Start without referral link
        await start_without_referer(message, bot, state)
    else:
        # Start with or without referral link
        await start_with_referer(message, bot, state, message.text) if ref else await start_without_referer(message,
                                                                                                            bot, state)


# Function to check subscription to all sponsor channels
async def handle_subscription_check(bot, message, db, state, split_message):
    # Get the list of channels from the database
    channels = await db.channels.find({})
    channels_list = [{'channel_id': channel.channel_id, 'url': channel.url, 'name': channel.name} for channel in
                     channels]
    # Check subscription to all channels
    all_subscribed = await check_all_subs(bot, message.from_user.id, channels_list)
    if all_subscribed:
        # Increment the subscription count
        await plus_sub(channels_list, db, message.from_user.id)
        # Handle start with or without a referral link
        await handle_start(message, bot, db, state, split_message)
    else:
        # Send a message prompting the user to subscribe
        callback = Start(message=message.text).pack()
        await not_subscribe(bot, message.from_user.id, channels_list, callback,
                            int(message.message_id) if message.message_id else None)


# Function for reply action
async def reply_action(message, bot, state, data: dict, referer: int, sender: int):
    keyboard_referer = InlineKeyboardBuilder()
    keyboard_referer.row(
        InlineKeyboardButton(text='Моя ссылка', callback_data=GetLink(referer=int(referer), check_my=True).pack()))
    keyboard_sender = InlineKeyboardBuilder()
    keyboard_sender.row(
        InlineKeyboardButton(text='Получить ссылку', callback_data=GetLink(referer=int(referer), check_my=False).pack()))
    
    # Отправляем медиафайл или текст в зависимости от типа сообщения
    if message.photo:
        # Если это фото
        photo = message.photo[-1].file_id  # Берем фото в максимальном разрешении
        caption = '<b>📬 Ответ на ваше анонимное сообщение:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>'
        await bot.send_photo(chat_id=int(sender), photo=photo, caption=caption,
                             parse_mode='html', reply_markup=keyboard_sender.as_markup())
    elif message.video:
        # Если это видео
        video = message.video.file_id
        caption = '<b>📬 Ответ на ваше анонимное сообщение:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>'
        await bot.send_video(chat_id=int(sender), video=video, caption=caption,
                             parse_mode='html', reply_markup=keyboard_sender.as_markup())
    elif message.document:
        # Если это документ
        document = message.document.file_id
        caption = '<b>📬 Ответ на ваше анонимное сообщение:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>'
        await bot.send_document(chat_id=int(sender), document=document, caption=caption,
                                parse_mode='html', reply_markup=keyboard_sender.as_markup())
    elif message.audio:
        # Если это аудио
        audio = message.audio.file_id
        caption = '<b>📬 Ответ на ваше анонимное сообщение:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>'
        await bot.send_audio(chat_id=int(sender), audio=audio, caption=caption,
                             parse_mode='html', reply_markup=keyboard_sender.as_markup())
    elif message.voice:
        # Если это голосовое сообщение
        voice = message.voice.file_id
        caption = '<b>📬 Ответ на ваше анонимное сообщение:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>'
        await bot.send_voice(chat_id=int(sender), voice=voice, caption=caption,
                             parse_mode='html', reply_markup=keyboard_sender.as_markup())
    elif message.video_note:
        # Если это видео-сообщение
        video_note = message.video_note.file_id
        await bot.send_video_note(chat_id=int(sender), video_note=video_note,
                                  reply_markup=keyboard_sender.as_markup())
    elif message.sticker:
        # Если это стикер
        sticker = message.sticker.file_id
        await bot.send_sticker(chat_id=int(sender), sticker=sticker,
                               reply_markup=keyboard_sender.as_markup())
    else:
        # Если это текст или другие типы сообщений
        # Подготовим объединенное сообщение для отправки
        if new_message:
            # Если есть фото для нового сообщения, отправим его с объединенным текстом
            await bot.send_photo(chat_id=int(sender), photo=new_message,
                                 caption='<b>📬 Ответ на ваше анонимное сообщение:</b>\n\n'
                                         f'<i>{message.text}</i>\n\n'
                                         '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>',
                                 parse_mode='html', reply_markup=keyboard_sender.as_markup())
        else:
            # Если нет фото, отправим текстовое сообщение с объединенным контентом
            combined_text = '<b>📬 Ответ на ваше анонимное сообщение:</b>\n\n'
            if message.text:
                combined_text += f'<i>{message.text}</i>\n\n'
            elif message.caption:
                combined_text += f'<i>{message.caption}</i>\n\n'
            combined_text += '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>'
            
            await bot.send_message(chat_id=int(sender),
                                   text=combined_text,
                                   parse_mode='html', reply_markup=keyboard_sender.as_markup())
    
    # Отправим пользователю уведомление об отправке ответа
    if answer_sended:
        await bot.send_photo(chat_id=message.from_user.id, photo=answer_sended,
                             caption='<b>📨 Ваш ответ был успешно отправлен!</b>',
                             parse_mode='html', reply_markup=keyboard_referer.as_markup())
    else:
        await bot.send_message(chat_id=message.from_user.id,
                               text='<b>📨 Ваш ответ был успешно отправлен!</b>',
                               parse_mode='html', reply_markup=keyboard_referer.as_markup())


# Function for send action
async def send_action(message, bot, state, data: dict, referer: int):
    keyboard_sender = InlineKeyboardBuilder()
    keyboard_sender.row(
        InlineKeyboardButton(text='Получить ссылку', callback_data=GetLink(referer=int(referer), check_my=False).pack()))
    keyboard_sender.row(
        InlineKeyboardButton(text='Отправить снова', callback_data=SendAgain(referer=int(referer), action='send').pack()))
    
    # Создаем клавиатуру с кнопкой Reply
    keyboard_referer = InlineKeyboardBuilder()
    keyboard_referer.row(InlineKeyboardButton(text='Reply',
                                             callback_data=Reply(sender=int(message.from_user.id), action='reply',
                                                                 referer=int(referer),
                                                                 reply_message=message.message_id).pack()))
    
    # Отправляем медиафайл или текст в зависимости от типа сообщения
    if message.photo:
        # Если это фото
        photo = message.photo[-1].file_id  # Берем фото в максимальном разрешении
        caption = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💬 <b>Вы можете ответить на это сообщение!</b>'
        await bot.send_photo(chat_id=int(referer), photo=photo, caption=caption,
                             parse_mode='html', reply_markup=keyboard_referer.as_markup())
    elif message.video:
        # Если это видео
        video = message.video.file_id
        caption = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💬 <b>Вы можете ответить на это сообщение!</b>'
        await bot.send_video(chat_id=int(referer), video=video, caption=caption,
                             parse_mode='html', reply_markup=keyboard_referer.as_markup())
    elif message.document:
        # Если это документ
        document = message.document.file_id
        caption = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💬 <b>Вы можете ответить на это сообщение!</b>'
        await bot.send_document(chat_id=int(referer), document=document, caption=caption,
                                parse_mode='html', reply_markup=keyboard_referer.as_markup())
    elif message.audio:
        # Если это аудио
        audio = message.audio.file_id
        caption = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💬 <b>Вы можете ответить на это сообщение!</b>'
        await bot.send_audio(chat_id=int(referer), audio=audio, caption=caption,
                             parse_mode='html', reply_markup=keyboard_referer.as_markup())
    elif message.voice:
        # Если это голосовое сообщение
        voice = message.voice.file_id
        caption = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
        if message.caption:
            caption += f'<i>{message.caption}</i>\n\n'
        caption += '💬 <b>Вы можете ответить на это сообщение!</b>'
        await bot.send_voice(chat_id=int(referer), voice=voice, caption=caption,
                             parse_mode='html', reply_markup=keyboard_referer.as_markup())
    elif message.video_note:
        # Если это видео-сообщение
        video_note = message.video_note.file_id
        await bot.send_video_note(chat_id=int(referer), video_note=video_note,
                                  reply_markup=keyboard_referer.as_markup())
    elif message.sticker:
        # Если это стикер
        sticker = message.sticker.file_id
        await bot.send_sticker(chat_id=int(referer), sticker=sticker,
                               reply_markup=keyboard_referer.as_markup())
    else:
        # Если это текст или другие типы сообщений
        # Подготовим объединенное сообщение для отправки получателю сначала
        if new_message:
            # Если есть фото для нового сообщения, отправим его с объединенным текстом
            caption_text = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
            if message.text:
                caption_text += f'<i>{message.text}</i>\n\n'
            elif message.caption:
                caption_text += f'<i>{message.caption}</i>\n\n'
            caption_text += '💬 <b>Вы можете ответить на это сообщение!</b>'
            
            await bot.send_photo(chat_id=int(referer), photo=new_message,
                                 caption=caption_text,
                                 parse_mode='html', reply_markup=keyboard_referer.as_markup())
        else:
            # Если нет фото, отправим текстовое сообщение с объединенным контентом
            combined_text = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
            if message.text:
                combined_text += f'<i>{message.text}</i>\n\n'
            elif message.caption:
                combined_text += f'<i>{message.caption}</i>\n\n'
            combined_text += '💬 <b>Вы можете ответить на это сообщение!</b>'
            
            await bot.send_message(chat_id=int(referer),
                                   text=combined_text,
                                   parse_mode='html', reply_markup=keyboard_referer.as_markup())
    
    # Отправим пользователю уведомление об отправке сообщения
    if send_message_photo:
        await bot.send_photo(chat_id=message.from_user.id, photo=send_message_photo,
                             caption='<b>✅ Ваше анонимное сообщение было успешно отправлено!</b>\n\n'
                                     '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>',
                             parse_mode='html', reply_markup=keyboard_sender.as_markup())
    else:
        await bot.send_message(chat_id=message.from_user.id,
                               text='<b>✅ Ваше анонимное сообщение было успешно отправлено!</b>\n\n'
                                    '💌 <b>Хотите получать анонимные сообщения тоже? Нажмите ⬇️</b>',
                               parse_mode='html', reply_markup=keyboard_sender.as_markup())


# Function to start with referral link
async def start_with_referer(message, bot, state, text):
    if message.from_user.id != int(text.split('/start ')[1]):
        # Send a welcome message that the user has come via referral link
        me = await bot.get_me()
        personal_link = f"https://t.me/{me.username}?start={message.from_user.id}"
        
        welcome_text = (
            "🎉 <b>Добро пожаловать в бот анонимных вопросов!</b>\n\n"
            "💬 <b>Вы перешли по чужой ссылке и можете отправить анонимное сообщение.</b>\n\n"
            "💌 <i>После отправки вашего сообщения, вы также сможете получить персональную ссылку для получения анонимных вопросов</i>"
        )
                
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text='📤 Поделиться своей ссылкой', callback_data=f'share_link:{message.from_user.id}'))
                
        res = await bot.send_message(chat_id=message.from_user.id, text=welcome_text, reply_markup=keyboard.as_markup())
        await state.set_state(SendMessage.send_message)
        await state.update_data(referer=text.split('/start ')[1], action='send', message_id=res.message_id)


# Function to start without referral link
async def start_without_referer(message, bot, state):
    me = await bot.get_me()
    personal_link = f"https://t.me/{me.username}?start={message.from_user.id}"
    
    welcome_text = (
        "🎉 <b>Добро пожаловать в бот анонимных вопросов!</b>\n\n"
        "💬 <b>Начните получать анонимные вопросы прямо сейчас!</b>\n\n"
        f"👉 <code>t.me/{me.username}?start={message.from_user.id}</code>\n\n"
        "💌 <i>Разместите эту ссылку ☝️ в описании своего профиля Telegram, TikTok, Instagram (stories), чтобы вам могли написать</i>"
    )
    
    if welcome:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text='📤 Поделиться ссылкой', callback_data=f'share_link:{message.from_user.id}'))
        
        await bot.send_photo(chat_id=message.from_user.id, photo=welcome,
                             caption=welcome_text,
                             reply_markup=keyboard.as_markup())
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text='📤 Поделиться ссылкой', callback_data=f'share_link:{message.from_user.id}'))
        
        await bot.send_message(chat_id=message.from_user.id,
                               text=welcome_text,
                               reply_markup=keyboard.as_markup())


# Function to check if the URL is a bot link
def is_bot_link(url):
    bot_link_pattern = re.compile(r'\?start=')
    return bool(bot_link_pattern.search(url))


# Function to check subscription to all sponsor channels
async def check_all_subs(bot, user_id, channels_list):
    try:
        for channel_info in channels_list:
            if is_bot_link(channel_info['url']):
                return True
            user_channel_status = await bot.get_chat_member(chat_id=channel_info['channel_id'], user_id=user_id)
            if user_channel_status.status not in ['administrator', 'owner', 'member', 'creator']:
                return False
        return True
    except:
        print(traceback.format_exc())
        return True


# Function to handle case when user is not subscribed
async def not_subscribe(bot, user_id, channels_list, callback, message_id):
    markup = InlineKeyboardBuilder()
    for channel in channels_list:
        markup.row(InlineKeyboardButton(text=channel['name'], url=channel['url'].replace(';', ':')))
    markup.row(InlineKeyboardButton(text='✅ Проверить подписку', callback_data=callback))
    try:
        if message_id is not None:
            await bot.edit_message_caption(chat_id=user_id, message_id=message_id,
                                           caption="🤖 <b>Чтобы использовать бота, подпишитесь на наших спонсоров:</b>\n\n"
                                                   "🔹 <i>Это необходимо для поддержки проекта</i>",
                                           reply_markup=markup.as_markup())
        else:
            print('Failed to check subscription')
    except:
        await bot.send_message(chat_id=user_id,
                               text="🤖 <b>Чтобы использовать бота, подпишитесь на наших спонсоров:</b>\n\n"
                                    "🔹 <i>Это необходимо для поддержки проекта</i>",
                               reply_markup=markup.as_markup())


# Function to increment subscription count for sponsor channels
async def plus_sub(channels_list, db, user_id):
    import time
    start_time = time.time()
    
    # Подготовим bulk операции для обновления каналов
    bulk_operations = []
    
    for channel in channels_list:
        # Используем update_one с upsert=False и применяем операции атомарно
        update_operation = {
            'filter': {'channel_id': channel['channel_id']},
            'update': {
                '$inc': {'subs': 1},  # Увеличиваем счетчик подписчиков
                '$addToSet': {'subscribed_users': user_id} # Добавляем пользователя в список, если его там еще нет
            }
        }
        bulk_operations.append(update_operation)
    
    # Выполняем bulk операции
    for operation in bulk_operations:
        await db.channels.update_one(operation['filter'], operation['update'])
    
    # Логируем операцию
    perf_logger.log_db_operation("plus_sub_bulk_update", "channels", time.time() - start_time, len(bulk_operations))


# Function to show advertisement to user
async def adv_show(user_id, bot, db):
    start_time = time.time()
    
    # Используем Redis кэш для хранения adv_id пользователя
    from src.utils.redis_cache import RedisCache
    cache = RedisCache()
    
    # Попробуем получить adv_id из кэша
    cached_adv_id = await cache.get(f"user_adv_id_{user_id}")
    
    if cached_adv_id is not None:
        adv_user_shows = cached_adv_id
    else:
        # Если в кэше нет, получаем из базы данных
        user_query = await db.users.find_one({'id': int(user_id)})
        if not user_query:
            perf_logger.log_db_operation("find_one", "users", time.time() - start_time, success=False)
            return # Если пользователь не найден, выходим
        
        adv_user_shows = int(user_query.adv_id)
        # Сохраняем в кэш на 1 час
        await cache.set(f"user_adv_id_{user_id}", adv_user_shows, 3600)
    
    # Получаем рекламный пост из базы данных
    adv_start_time = time.time()
    if adv_user_shows != 1:
        adv_query = await db.adv.find_one({'adv_id': adv_user_shows})
    else:
        adv_query = await db.adv.find_one_with_min_adv_id()
    
    perf_logger.log_db_operation("find_one/find_one_with_min_adv_id", "adv", time.time() - adv_start_time)
    
    if adv_query:
        # Получаем следующий рекламный пост
        next_adv_start_time = time.time()
        next_adv_query = await db.adv.find_one_with_next_adv_id(adv_query.adv_id)
        perf_logger.log_db_operation("find_one_with_next_adv_id", "adv", time.time() - next_adv_start_time)
        
        if next_adv_query:
            new_adv_id = int(next_adv_query.adv_id)
        else:
            new_adv_id = 1  # Если следующего поста нет, возвращаемся к первому
        
        # Обновляем adv_id пользователя в базе данных и в кэше
        update_start_time = time.time()
        await db.users.update_one({'id': int(user_id)}, {'adv_id': new_adv_id})
        perf_logger.log_db_operation("update_one", "users", time.time() - update_start_time)
        
        await cache.set(f"user_adv_id_{user_id}", new_adv_id, 3600)
        
        kwargs = {'caption': adv_query.caption} if adv_query.caption else {}
        if adv_query.content_type == 'photo':
            await bot.send_photo(user_id, photo=adv_query.content, **kwargs, parse_mode='html')
        elif adv_query.content_type == 'video':
            await bot.send_video(user_id, video=adv_query.content, **kwargs, parse_mode='html')
        elif adv_query.content_type == 'document':
            await bot.send_document(user_id, document=adv_query.content, **kwargs, parse_mode='html')
        elif adv_query.content_type == 'text':
            await bot.send_message(user_id, text=adv_query.content, parse_mode='html')
    
    perf_logger.log_db_operation("adv_show_total", "performance", time.time() - start_time)


async def show_advert(user_id: int):
    # Show advert func
    ...


def get_referral_id_from_env():
    """
    Получает реф ID из переменной окружения
    """
    # Получаем основной реф ID
    referral_ids = []
    main_referral_id = os.getenv("REFERRAL_ID")
    if main_referral_id:
        referral_ids.append(int(main_referral_id))
    
    # Проверяем дополнительные реф ID (до 10)
    for i in range(2, 11):
        additional_referral_id = os.getenv(f"REFERRAL_ID_{i}")
        if additional_referral_id:
            referral_ids.append(int(additional_referral_id))
        else:
            # Если переменная не установлена, прерываем цикл
            break
    
    return referral_ids


async def track_referral_usage(referrer_id: int, user_info: dict, message_content: str = None):
    """
    Создает запись о пользователе, который перешел по реф ссылке
    """
    # Логируем информацию для отладки
    print(f"Tracking referral usage: referrer_id={referrer_id}, user_id={user_info['id']}, message_content={message_content}")
    
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
    from src.utils.db import db  # Импорт в глобальной области видимости для избежания циклических зависимостей
    try:
        result = await db.referral_tracking.insert_one(referral_tracking.dict())
        print(f"Referral tracking record inserted with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error inserting referral tracking record: {e}")
    
    return referral_tracking


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
