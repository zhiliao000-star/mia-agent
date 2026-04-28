from typing import Any

import httpx

from mia.settings import Settings


class SendBlueClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_message(self, *, number: str, content: str) -> dict[str, Any]:
        if not self.settings.sendblue_api_key_id or not self.settings.sendblue_api_secret_key:
            raise RuntimeError("Missing SendBlue API credentials")
        if not self.settings.sendblue_from_number:
            raise RuntimeError("Missing SENDBLUE_FROM_NUMBER")

        body: dict[str, Any] = {
            "content": content,
            "from_number": self.settings.sendblue_from_number,
            "number": number,
        }
        if self.settings.sendblue_status_callback:
            body["status_callback"] = self.settings.sendblue_status_callback

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{str(self.settings.sendblue_api_base_url).rstrip('/')}/api/send-message",
                headers={
                    "Content-Type": "application/json",
                    "sb-api-key-id": self.settings.sendblue_api_key_id,
                    "sb-api-secret-key": self.settings.sendblue_api_secret_key,
                },
                json=body,
            )
            response.raise_for_status()
            return response.json()
