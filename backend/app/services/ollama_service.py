import httpx

from app.config import settings


OLLAMA_URL = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
OLLAMA_MODEL = settings.OLLAMA_MODEL

# CPU inference on a small Azure VM can take several minutes for long prompts.
_client = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0))


async def generate_response(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.2,
            "num_predict": 384,
        },
    }
    response = await _client.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    answer = data.get("response")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Ollama returned an empty response")
    return answer.strip()
