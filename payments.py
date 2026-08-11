import aiohttp
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from config import CRYPTOBOT_TOKEN, XROCKET_TOKEN, XROCKET_WEBHOOK_URL

logger = logging.getLogger(__name__)


# ==================== CryptoBot ====================
class CryptoBotPay:
    BASE_URL = "https://pay.crypt.bot/api"

    def __init__(self, token: str):
        self.token = token
        self.headers = {"Crypto-Pay-API-Token": token}

    async def create_invoice(self, amount: float, comment: str = "") -> Optional[Dict]:
        """Создание инвойса в CryptoBot"""
        async with aiohttp.ClientSession() as session:
            data = {
                "amount": amount,
                "currency_type": "crypto",
                "asset": "USDT",  # или другая криптовалюта
                "description": comment,
                "expires_in": 3600  # час на оплату
            }

            try:
                async with session.post(
                        f"{self.BASE_URL}/createInvoice",
                        headers=self.headers,
                        json=data
                ) as resp:
                    result = await resp.json()
                    if result.get("ok"):
                        return {
                            "invoice_id": result["result"]["invoice_id"],
                            "pay_url": result["result"]["pay_url"],
                            "status": result["result"]["status"]
                        }
                    else:
                        logger.error(f"CryptoBot error: {result}")
                        return None
            except Exception as e:
                logger.error(f"CryptoBot exception: {e}")
                return None

    async def check_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Проверка статуса инвойса"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f"{self.BASE_URL}/getInvoices",
                        headers=self.headers,
                        json={"invoice_ids": [invoice_id]}
                ) as resp:
                    result = await resp.json()
                    if result.get("ok") and result["result"]["items"]:
                        return result["result"]["items"][0]
                    return None
            except Exception as e:
                logger.error(f"CryptoBot check exception: {e}")
                return None


# ==================== xRocket ====================
class XRocketPay:
    BASE_URL = "https://pay.xrocket.exchange"

    def __init__(self, token: str):
        self.token = token
        self.headers = {"Rocket-Pay-Key": token}

    async def create_invoice(self, amount: float, comment: str = "") -> Optional[Dict]:
        """Создание инвойса в xRocket"""
        async with aiohttp.ClientSession() as session:
            data = {
                "amount": amount,
                "currency": "USDT",  # или другая валюта
                "currencyType": "crypto",
                "expiresIn": 3600,
                "comment": comment,
                "webhookUrl": XROCKET_WEBHOOK_URL
            }

            try:
                async with session.post(
                        f"{self.BASE_URL}/tg-invoices",
                        headers=self.headers,
                        json=data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {
                            "invoice_id": result["id"],
                            "pay_url": result["link"],
                            "status": result["status"]
                        }
                    else:
                        logger.error(f"xRocket error: {await resp.text()}")
                        return None
            except Exception as e:
                logger.error(f"xRocket exception: {e}")
                return None

    async def check_invoice(self, invoice_id: str) -> Optional[Dict]:
        """Проверка статуса инвойса"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        f"{self.BASE_URL}/tg-invoices/{invoice_id}",
                        headers=self.headers
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
            except Exception as e:
                logger.error(f"xRocket check exception: {e}")
                return None

    @staticmethod
    def verify_webhook_signature(body: bytes, signature: str, token: str) -> bool:
        """Проверка подписи вебхука от xRocket"""
        secret = hashlib.sha256(token.encode()).hexdigest()
        expected = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# Создаем экземпляры платежных систем
crypto_bot = CryptoBotPay(CRYPTOBOT_TOKEN)
xrocket = XRocketPay(XROCKET_TOKEN)