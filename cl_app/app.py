# cl_app/app.py
import chainlit as cl

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="Welcome from Chainlit 2.9.3 👋").send()

@cl.on_message
async def on_message(message: cl.Message):
    await cl.Message(content=f"You said: {message.content}").send()
