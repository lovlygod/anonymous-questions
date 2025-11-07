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