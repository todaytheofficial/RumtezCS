import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Today_Idk:TpdauT434odayTodayToday23@cluster0.rlgkop5.mongodb.net/rumtezcs_bot?retryWrites=true&w=majority&appName=Cluster0")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "rumtezcs_bot")