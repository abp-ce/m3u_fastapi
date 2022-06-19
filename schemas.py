from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class UserFromForm(User):
    password: str


class PersonalList(BaseModel):
    title: str
    value: str


class Programme_Response(BaseModel):
    disp_name: str
    pstart: datetime
    pstop: datetime
    title: str
    pdesc: Optional[str] = None

    class Config:
        orm_mode = True


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


class tgrmLocation(BaseModel):
    longitude: float
    latitude: float


class tgrmMessage(BaseModel):
    message_id: int
    from_: Optional[tgrmUser] = None
    sender_chat: Optional[tgrmChat] = None
    date: datetime
    chat: Optional[tgrmChat] = None
    forward_from: Optional[tgrmUser] = None
    text: Optional[str] = None
    location: Optional[tgrmLocation] = None

    class Config:
        fields = {
            'from_': 'from'
        }


class tgrmCallbackQuery(BaseModel):
    id: str
    from_: tgrmUser = Field(..., alias='from')
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
    callback_data: Optional[str] = None  # Union must be???


class tgrmKeyboardButton(BaseModel):
    text: str
    request_contact: Optional[bool] = None
    request_location: Optional[bool] = None


class tgrmReplyKeyboardRemove(BaseModel):
    tag: Literal['Remove']
    remove_keyboard: Optional[bool] = True


class tgrmReplyKeyboardMarkup(BaseModel):
    tag: Literal['Reply']
    keyboard: List[List[tgrmKeyboardButton]] = None
    resize_keyboard: Optional[bool] = None
    one_time_keyboard: Optional[bool] = None


class tgrmInlineKeyboardMarkup(BaseModel):
    tag: Literal['Inline']
    inline_keyboard: List[List[tgrmInlineKeyboardButton]] = None


"""
class tgrmSendMessage(BaseModel):
    chat_id: Union[int, str]
    text: str
    parse_mode: Optional[str] = None
    reply_markup: Optional[Union[
        tgrmReplyKeyboardMarkup,
        tgrmInlineKeyboardMarkup,
        tgrmReplyKeyboardRemove
    ]] = None
"""
# class tgrmResponse(tgrmSendMessage):


class tgrmSendMessage(BaseModel):
    method: Optional[str] = None
    chat_id: Union[int, str]
    text: str
    parse_mode: Optional[str] = None
    reply_markup: Optional[Union[
        tgrmReplyKeyboardMarkup,
        tgrmInlineKeyboardMarkup,
        tgrmReplyKeyboardRemove
    ]] = None
