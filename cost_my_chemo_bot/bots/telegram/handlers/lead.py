import httpx
from aiogram import types
from aiogram.dispatcher import FSMContext
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, messages
from cost_my_chemo_bot.bots.telegram.state import Form
from cost_my_chemo_bot.config import SETTINGS

logger = getLogger(__name__)


async def save_lead(message: types.Message):
    async with httpx.AsyncClient(base_url=SETTINGS.BITRIX_URL) as client:
        client.post(
            "",
            params={
                "FIELDS[TITLE]": "Новый лид",
                "FIELDS[NAME]": message.contact.first_name,
                "FIELDS[LAST_NAME": message.contact.last_name,
                # Telegram contact doesn't have an email
                # "FIELDS[EMAIL][0][VALUE]": message.contact.email,
                # "FIELDS[EMAIL][0][VALUE_TYPE]": "WORK",
                "FIELDS[PHONE][0][VALUE]": message.contact.phone_number,
                "FIELDS[PHONE][0][VALUE_TYPE]": "TELEGRAM",
            },
        )


@dispatcher.dp.message_handler(state=Form.lead, content_types=types.ContentType.CONTACT)
async def process_lead(message: types.Message, state: FSMContext):
    logger.info("%s", message.contact)
    await state.update_data(lead=message.contact.as_json())
    await state.set_state(None)
    await message.reply(messages.THANKS, reply_markup=types.ReplyKeyboardRemove())
