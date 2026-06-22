import httpx
from app.core.config import settings


class DifyService:
    """封装所有对 Dify Cloud API 的调用"""

    def __init__(self):
        self.base_url = settings.dify_api_base
        self.api_key = settings.dify_api_key
        self.dataset_id = settings.dify_dataset_id
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def upload_document(self, filename: str, file_content: bytes, content_type: str) -> dict:
        url = f"{self.base_url}/datasets/{self.dataset_id}/document/create-by-file"
        headers = {"Authorization": f"Bearer {settings.dify_dataset_api_key}"}
        files = {"file": (filename, file_content, content_type)}
        data = {
            "data": '{"indexing_technique":"high_quality","process_rule":{"mode":"automatic"}}'
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
        if response.status_code != 200:
            print(f"[Dify ERROR] status={response.status_code}, body={response.text}")
            raise Exception(f"Dify 上传失败：{response.text}")
        return response.json()

    async def chat_stream(self, question: str, conversation_id: str = None):
        """
        流式对话，是一个异步生成器
        每次 yield 一行 SSE 数据，直接透传给前端
        """
        url = f"{self.base_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {},
            "query": question,
            "response_mode": "streaming",
            "conversation_id": conversation_id or "",
            "user": "patient",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error = await response.aread()
                    raise Exception(f"Dify 对话失败：{error.decode()}")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n\n"


# 全局单例
dify_service = DifyService()