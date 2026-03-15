import json
import os
import firebase_admin
from firebase_admin import credentials, firestore_async
from config import settings

_db = None


def get_db():
    return _db


def _get_credentials():
    # 1. FIREBASE_CREDENTIALS_JSON env var (Railway - to'g'ri yo'l)
    raw = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if raw.startswith("{"):
        cred_dict = json.loads(raw)
        print("✅ Firebase: FIREBASE_CREDENTIALS_JSON dan yuklandi")
        return credentials.Certificate(cred_dict)

    # 2. FIREBASE_CREDENTIALS_PATH o'zi JSON string bo'lsa
    path = settings.FIREBASE_CREDENTIALS_PATH.strip()
    if path.startswith("{"):
        cred_dict = json.loads(path)
        print("✅ Firebase: PATH ichidagi JSON dan yuklandi")
        return credentials.Certificate(cred_dict)

    # 3. Lokal fayl
    print(f"✅ Firebase: {path} fayldan yuklandi")
    return credentials.Certificate(path)


async def connect_db():
    global _db
    if not firebase_admin._apps:
        cred = _get_credentials()
        firebase_admin.initialize_app(cred)
    _db = firestore_async.client()
    print(f"✅ Firebase Firestore ga ulandi: {settings.FIREBASE_PROJECT_ID}")


async def close_db():
    global _db
    _db = None
    print("❌ Firebase ulanishi yopildi")
