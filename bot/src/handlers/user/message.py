from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
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
        await handle_start(message, bot, db, state, split_message)
    else:
        await handle_subscription_check(bot, message, db, state, split_message)
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
        await message.answer("Команды недоступны в режиме отправки сообщения. Команда отменена.")
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
        await message.answer("❗️ Unable to send message, referer is missing.")
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
        await message.answer("Неизвестная команда. Используйте /start для начала работы с ботом.")
    else:
        # If user is in FSM state, ignore the command
        await message.answer("Команды недоступны в режиме отправки сообщения.")

# Handle all other messages when not in FSM state - provide helpful response
@router.message()
async def handle_other_messages(message: Message, bot: Bot, db: MongoDbClient, state: FSMContext):
    # Check if user is in FSM state
    current_state = await state.get_state()
    if current_state == SendMessage.send_message:
        # If user is in message sending state, this will be handled by send_message handler
        # This is a fallback to ensure messages are processed correctly
        await message.answer("Пожалуйста, завершите текущую операцию или используйте /start для отмены.")
    else:
        # If user sends a message outside of FSM state, provide helpful response
        await message.answer("Для отправки анонимного сообщения перейдите по персональной ссылке или используйте /start")
