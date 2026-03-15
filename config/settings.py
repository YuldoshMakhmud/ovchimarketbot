from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    BOT_TOKEN: str
    ADMIN_IDS: str = ""

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"
    FIREBASE_PROJECT_ID: str = "sohibjonovchi"

    # To'lov karta ma'lumotlari
    CARD_NUMBER: str = "0000 0000 0000 0000"
    CARD_OWNER: str = "Karta egasi"

    # Shop
    SHOP_NAME: str = "Ovchi Market"
    SHOP_CURRENCY: str = "UZS"
    MIN_ORDER_AMOUNT: int = 10000

    # Webhook
    WEBHOOK_HOST: str = ""
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_PORT: int = 8080

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]


settings = Settings()
