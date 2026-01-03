# cl_app/app.py
import chainlit as cl

from app.db.db import get_db_standalone
from app.crud.sessions import create_session_record


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="Welcome from Chainlit 2.9.3 👋").send()

@cl.on_message
async def on_message(message: cl.Message):
    with get_db_standalone() as db:
        create_session_record(db, user_id="default", title=message.content)

    await cl.Message(content=f"You said: {message.content}").send()
