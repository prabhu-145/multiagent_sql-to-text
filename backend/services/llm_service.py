import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def generate_response(prompt, model="phi3"):

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload
    )

    data = response.json()

    return data["response"]