import os
import logging
import time
from datetime import datetime
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, CallbackQuery, InlineKeyboardButton, InputMediaPhoto, InputMediaAnimation, \
    Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.callbacks import AdminStats, AdminUpload, AdminMailing, AdminChannels, AdminRefs, AdminAdv

router = Router()


# Admin-panel keyboard
@router.message(Command('admin'))
async def admin_panel(message: Message):
    # Check if the user ID matches the admin IDs
    admin_id_1 = int(os.getenv("ADMIN_ID_1"))
    admin_id_2 = int(os.getenv("ADMIN_ID_2"))
    if message.from_user.id == admin_id_1 or message.from_user.id == admin_id_2:
        keyboard_admin = InlineKeyboardBuilder()

        # Add buttons to the keyboard for different admin actions
        keyboard_admin.row(
            InlineKeyboardButton(text='Статистика📊', callback_data=AdminStats().pack()),
            InlineKeyboardButton(text='Загрузить📝', callback_data=AdminUpload().pack())
        )
        keyboard_admin.row(
            InlineKeyboardButton(text='Рассылка📩', callback_data=AdminMailing().pack()),
            InlineKeyboardButton(text='Каналы🗣️', callback_data=AdminChannels().pack())
        )
        keyboard_admin.row(
            InlineKeyboardButton(text='Рефералы🔗', callback_data=AdminRefs().pack()),
            InlineKeyboardButton(text='Рекламный пост📢', callback_data=AdminAdv().pack())
        )

        # Send the admin panel message with the keyboard
        await message.answer("Панель администратора:", reply_markup=keyboard_admin.as_markup())
