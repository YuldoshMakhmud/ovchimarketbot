import json
import os
import firebase_admin
from firebase_admin import credentials, firestore_async
from config import settings

_db = None


def get_db():
    return _db


def _get_credentials():
    """
    Firebase credentials olish:
    1. FIREBASE_CREDENTIALS_JSON env var (Railway)
    2. FIREBASE_CREDENTIALS_PATH fayl (lokal)
    3. FIREBASE_CREDENTIALS_PATH o'zi JSON string bo'lsa (Railway noto'g'ri sozlangan)
    """

    # 1. To'g'ri yo'l: FIREBASE_CREDENTIALS_JSON env var
    raw = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
    if raw and raw.strip().startswith("{"):
        raw = raw.replace('\\n', '\n')
        cred_dict = json.loads(raw)
        print("✅ Firebase: FIREBASE_CREDENTIALS_JSON dan yuklandi")
        return credentials.Certificate(cred_dict)

    # 2. FIREBASE_CREDENTIALS_PATH o'zi JSON string bo'lsa
    path = settings.FIREBASE_CREDENTIALS_PATH
    if path and path.strip().startswith("{"):
        path = path.replace('\\n', '\n')
        cred_dict = json.loads(path)
        print("✅ Firebase: FIREBASE_CREDENTIALS_PATH ichidagi JSON dan yuklandi")
        return credentials.Certificate(cred_dict)

    # 3. Lokal: fayl yo'li
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
