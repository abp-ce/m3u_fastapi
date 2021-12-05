from datetime import datetime
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field

class tgrmUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    can_join_groups: Optional[bool] = None
    can_read_all_group_messages: Optional[bool] = None
    supports_inline_queries: Optional[bool] = None

class tgrmChat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class tgrmMessage(BaseModel):
    message_id: int
    from_: Optional[tgrmUser] = None
    sender_chat: Optional[tgrmChat] = None
    date: datetime
    chat: Optional[tgrmChat] = None
    forward_from: Optional[tgrmUser] = None
    text: Optional[str] = None
    class Config: 
        fields = {
            'from_': 'from'
        }

class tgrmCallbackQuery(BaseModel):
    id: str
    from_: tgrmUser = Field(...,alias='from')
    message: Optional[tgrmMessage] = None
    inline_message_id: Optional[str] = None
    chat_instance: str
    data: Optional[str] = None
    game_short_name: Optional[str] = None

class tgrmUpdate(BaseModel):
    update_id: int
    message: Optional[tgrmMessage] = None
    callback_query: Optional[tgrmCallbackQuery] = None

class tgrmInlineKeyboardButton(BaseModel):
    text: str
    callback_data: Optional[str] = None

class tgrmInlineKeyboardMarkup(BaseModel):
    inline_keyboard: List[List[tgrmInlineKeyboardButton]] = None

class tgrmSendMessage(BaseModel):
    chat_id: Union[int, str]
    text: Optional[str] = None
    parse_mode: Optional[str] = None
    reply_markup: Optional[tgrmInlineKeyboardMarkup] = None

class tgrmResponse(tgrmSendMessage):
    method: str = 'sendMessage'