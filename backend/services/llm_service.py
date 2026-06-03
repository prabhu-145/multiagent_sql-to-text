import os
import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)


def generate_response(
    prompt: str,
    model: str | None = None,
    num_ctx: int = 4096,
    num_predict: int = 256,
    temperature: float = 0.1,
    timeout: int = 240
):
    selected_model = model or os.getenv("OLLAMA_MODEL", "mistral")

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": num_ctx,
            "num_predict": num_predict,
            "temperature": temperature
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=timeout
        )

        if response.status_code != 200:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text

            raise Exception(
                f"Ollama error response: {error_body}"
            )

        return response.json().get("response", "")

    except requests.exceptions.ReadTimeout:
        raise Exception(
            f"Ollama model '{selected_model}' timed out."
        )

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Cannot connect to Ollama. Make sure Ollama is running."
        )