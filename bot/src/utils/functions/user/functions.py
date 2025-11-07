import re
import traceback

import aiohttp
import logging
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.callbacks import Reply, SendAgain, GetLink, Start
from src.utils.fsm_state import SendMessage
from src.utils.photo import send_message_photo, new_message, answer_sended, welcome
from src.utils.text import hello_referer

log = logging.getLogger('adverts')


# Function to sort actions and send messages with referer
async def send_message_with_referer(message, bot, state, data: dict, referer: int, sender: int):
    message_id = data.get('message_id')
    if message_id:
        try:
            # Attempt to delete the message
            await bot.delete_message(chat_id=message.from_user.id, message_id=int(message_id))
        except:
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
    
    # Подготовим объединенное сообщение для отправки получателю сначала
    if new_message:
        # Если есть фото для нового сообщения, отправим его с объединенным текстом
        caption_text = '<b>📦 Новое анонимное сообщение для вас:</b>\n\n'
        if message.text:
            caption_text += f'<i>{message.text}</i>\n\n'
        elif message.caption:
            caption_text += f'<i>{message.caption}</i>\n\n'
        caption_text += '💬 <b>Вы можете ответить на это сообщение!</b>'
        
        # Создаем клавиатуру сначала
        keyboard_referer = InlineKeyboardBuilder()
        reply_message = await bot.copy_message(chat_id=int(referer), from_chat_id=message.from_user.id,
                                               message_id=message.message_id)
        keyboard_referer.row(InlineKeyboardButton(text='Ответить',
                                                  callback_data=Reply(sender=int(message.from_user.id), action='Ответить',
                                                                      referer=int(referer),
                                                                      reply_message=reply_message.message_id).pack()))
        
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
        
        # Создаем клавиатуру сначала
        keyboard_referer = InlineKeyboardBuilder()
        reply_message = await bot.copy_message(chat_id=int(referer), from_chat_id=message.from_user.id,
                                               message_id=message.message_id)
        keyboard_referer.row(InlineKeyboardButton(text='Ответить',
                                                  callback_data=Reply(sender=int(message.from_user.id), action='Ответить',
                                                                      referer=int(referer),
                                                                      reply_message=reply_message.message_id).pack()))
        
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
        keyboard.row(InlineKeyboardButton(text='📤 Поделиться своей ссылкой', switch_inline_query=personal_link))
                
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
        keyboard.row(InlineKeyboardButton(text='📤 Поделиться ссылкой', switch_inline_query=personal_link))
        
        await bot.send_photo(chat_id=message.from_user.id, photo=welcome,
                             caption=welcome_text,
                             reply_markup=keyboard.as_markup())
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text='📤 Поделиться ссылкой', switch_inline_query=personal_link))
        
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
    for channel in channels_list:
        current_channel = await db.channels.find_one({'channel_id': channel['channel_id']})
        if current_channel.subscribed_users:
            if user_id not in current_channel.subscribed_users:
                current_subs = current_channel.subs
                print(current_subs)
                current_channel.subscribed_users.append(user_id)
                print(current_channel.subscribed_users)
                new_subs = int(current_subs) + 1
                await db.channels.update_one(
                    {'channel_id': channel['channel_id']},
                    {'subs': new_subs, 'subscribed_users': current_channel.subscribed_users}
                )
            else:
                pass
        else:
            current_subs = current_channel.subs
            users_list = [user_id]
            new_subs = int(current_subs) + 1
            await db.channels.update_one(
                {'channel_id': channel['channel_id']},
                {'subs': new_subs, 'subscribed_users': users_list}
            )


# Function to show advertisement to user

async def adv_show(user_id, bot, db):
    user_query = await db.users.find_one({'id': int(user_id)})
    adv_user_shows = int(user_query.adv_id)
    if adv_user_shows != 1:
        adv_query = await db.adv.find_one({'adv_id': adv_user_shows})
    else:
        adv_query = await db.adv.find_one_with_min_adv_id()
    try:
        next_adv_query = await db.adv.find_one_with_next_adv_id(adv_query.adv_id)
        await db.users.update_one({'id': int(user_id)},
                                  {'adv_id': int(next_adv_query.adv_id)})
    except:
        adv_id = 1
        await db.users.update_one({'id': int(user_id)},
                                  {'adv_id': adv_id})
    if adv_query:
        kwargs = {'caption': adv_query.caption} if adv_query.caption else {}
        if adv_query.content_type == 'photo':
            await bot.send_photo(user_id, photo=adv_query.content, **kwargs, parse_mode='html')
        elif adv_query.content_type == 'video':
            await bot.send_video(user_id, video=adv_query.content, **kwargs, parse_mode='html')
        elif adv_query.content_type == 'document':
            await bot.send_document(user_id, document=adv_query.content, **kwargs, parse_mode='html')
        elif adv_query.content_type == 'text':
            await bot.send_message(user_id, text=adv_query.content, parse_mode='html')


async def show_advert(user_id: int):
    # Show advert func
    ...
