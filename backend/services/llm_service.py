import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def generate_response(prompt, model="phi3"):
    payload = {
    "model": model,
    "prompt": prompt,
    "stream": False,
    "options": {
        "num_ctx": 1024,
        "num_predict": 200
    }
}

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    data = response.json()

    if "response" not in data:
        raise Exception(f"Ollama error response: {data}")

    return data["response"]