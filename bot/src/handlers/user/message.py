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
    if user.first_start:
        # If this is the user's first start, update the database
        await db.users.update_one({'id': message.from_user.id}, {'first_start': False})
        # handle_start will send its own welcome message, so we don't need to send it here
        await handle_start(message, bot, db, state, split_message)
    else:
        await handle_subscription_check(bot, message, db, state, split_message)
        
        # Send welcome message with share button only when not from referral link
        me = await bot.get_me()
        personal_link = f"https://t.me/{me.username}?start={message.from_user.id}"
        
        welcome_text = (
            "🎉 <b>Добро пожаловать в бот анонимных вопросов!</b>\n\n"
            "💬 <b>Начните получать анонимные вопросы прямо сейчас!</b>\n\n"
            f"👉 <code>t.me/{me.username}?start={message.from_user.id}</code>\n\n"
            "💌 <i>Разместите эту ссылку ☝️ в описании своего профиля Telegram, TikTok, Instagram (stories), чтобы вам могли написать</i>"
        )
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text='📤 Поделиться ссылкой', switch_inline_query=personal_link))
        
        await message.answer(welcome_text, reply_markup=keyboard.as_markup())
    
    # Show advertisement
    await show_advert(message.from_user.id)
    await adv_show(message.from_user.id, bot, db)


# Handle admin command specifically to avoid processing it as a message to referer
@router.message(Command('admin'))
async def admin_command(message: Message, bot: Bot, db: MongoDbClient, state: FSMContext):
    # Clear FSM state if user is in message sending state
    current_state = await state.get_state()
    if current_state == SendMessage.send_message:
        await state.clear()
    # Forward to admin handler by importing and calling it
    from src.handlers.admin.message import admin_panel
    await admin_panel(message)


# Handle sending and replying to messages
@router.message(SendMessage.send_message)
async def send_message(message: Message, bot: Bot, db: MongoDbClient, state: FSMContext):
    # Check if the message is a command - if so, don't process as a message to referer
    if message.text and message.text.startswith('/'):
        # This is a command, clear the state and ignore
        await state.clear()
        await message.answer("❌ <b>Команды недоступны в режиме отправки сообщения.</b>\n\n"
                             "✅ <i>Операция отправки сообщения отменена.</i>")
        return
    
    # Get the FSM context data
    data = await state.get_data()
    if data.get('referer'):
        # If there is a referer, send the message with referer
        await send_message_with_referer(
            message, bot, state, data, int(data.get('referer')),
            int(data.get('sender')) if data.get('sender') else None
        )
    else:
        # If there is no referer, send an error message
        await message.answer("❗️ <b>Не удалось отправить сообщение.</b>\n\n"
                             "ℹ️ <i>Отсутствует получатель. Попробуйте начать сначала.</i>")
    # Show advertisement
    await show_advert(message.from_user.id)
    await adv_show(message.from_user.id, bot, db)
    # Clear the FSM state
    await state.clear()


# Handle all other commands when not in FSM state - ensure they are properly handled
@router.message(lambda message: message.text and message.text.startswith('/'))
async def handle_commands(message: Message, bot: Bot, db: MongoDbClient, state: FSMContext):
    # If user sends a command but it's not handled by other handlers, provide helpful response
    current_state = await state.get_state()
    if current_state != SendMessage.send_message:
        await message.answer("🤖 <b>Неизвестная команда.</b>\n\n"
                             "💡 <i>Используйте /start для начала работы с ботом.</i>")
    else:
        # If user is in FSM state, ignore the command
        await message.answer("❌ <b>Команды недоступны в режиме отправки сообщения.</b>\n\n"
                             "ℹ️ <i>Пожалуйста, завершите текущую операцию или используйте /start для отмены.</i>")


# Handle all other messages when not in FSM state - provide helpful response
@router.message()
async def handle_other_messages(message: Message, bot: Bot, db: MongoDbClient, state: FSMContext):
    # Check if user is in FSM state
    current_state = await state.get_state()
    if current_state == SendMessage.send_message:
        # If user is in message sending state, this will be handled by send_message handler
        # This is a fallback to ensure messages are processed correctly
        await message.answer("💬 <b>Введите ваше сообщение для отправки.</b>\n\n"
                             "❌ <i>Для отмены операции используйте /start</i>")
    else:
        # If user sends a message outside of FSM state, provide helpful response
        await message.answer("📩 <b>Для отправки анонимного сообщения:</b>\n\n"
                             "🔹 <i>Перейдите по персональной ссылке от получателя</i>\n"
                             "🔹 <i>Или используйте команду /start для начала работы</i>")
