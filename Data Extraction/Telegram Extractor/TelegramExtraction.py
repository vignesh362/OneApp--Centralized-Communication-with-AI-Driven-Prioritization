from pymongo import MongoClient
from datetime import datetime
from telethon import TelegramClient, events
import asyncio
import configparser
from telethon.sessions import MemorySession

# MongoDB connection setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["telegram_db"]
messages_collection = db["messages"]

# Read configuration and set up Telegram client
config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
phone_number = config['Telegram']['phone_number']

client = TelegramClient(MemorySession(), api_id, api_hash)

async def start_client():
    await client.start(phone=phone_number)
    print("Client Created")

async def upload_messages_to_mongodb():
    dialogs = await client.get_dialogs()

    for dialog in dialogs:
        chat_name = dialog.name
        chat_type = "group" if dialog.is_group else "dm"

        async for message in client.iter_messages(dialog.entity, limit=10):
            message_data = {
                "sender": message.sender.first_name if message.sender else "Unknown",
                "time": message.date,
                "message": message.text,
                "type": chat_type,
                "chat_name": chat_name
            }
            messages_collection.insert_one(message_data)

    print("Messages uploaded to MongoDB.")

async def main():
    await start_client()
    await upload_messages_to_mongodb()
    await client.disconnect()

asyncio.run(main())