import httpx


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

# Reuse the connection pool between intent and answer generation.
_client = httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=5.0))


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
