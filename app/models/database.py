import json
import os
import firebase_admin
from firebase_admin import credentials, firestore_async
from config import settings

_db = None


def get_db():
    return _db


async def connect_db():
    global _db
    if not firebase_admin._apps:
        firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

        if firebase_creds_json:
            # Railway: env variable dan JSON parse qilish
            # \\n -> \n ga o'zgartirish (Railway escape qiladi)
            firebase_creds_json = firebase_creds_json.replace('\\n', '\n')
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            print("✅ Firebase credentials env variable dan yuklandi")
        else:
            # Lokal: JSON fayldan yuklash
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            print("✅ Firebase credentials fayldan yuklandi")

        firebase_admin.initialize_app(cred)

    _db = firestore_async.client()
    print(f"✅ Firebase Firestore ga ulandi: {settings.FIREBASE_PROJECT_ID}")


async def close_db():
    global _db
    _db = None
    print("❌ Firebase ulanishi yopildi")
