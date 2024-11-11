import httpx

class ChatAPIClient:
    def __init__(self, base_url="http://api:8000"):
        self.base_url = base_url

    async def get_chat_history(self) -> list:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/chat/history")
                response.raise_for_status()
                return response.json().get("history", [])
            except Exception as e:
                return []

    async def send_message(self, message: str, context: dict) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat",
                    json={"message": message, "context": context},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"response": f"Erro na comunicação: {str(e)}", "metadata": {"error": str(e)}}
