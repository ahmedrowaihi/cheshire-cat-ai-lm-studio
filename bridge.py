from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import json
from fastapi.responses import JSONResponse
import logging

# Configuration
BRIDGE_PORT = 6000
LM_STUDIO_URL = "http://host.docker.internal:1234/v1/chat/completions"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class CheshireRequest(BaseModel):
    text: str


class CheshireResponse(BaseModel):
    text: str


@app.post("/", response_model=CheshireResponse)
async def bridge_request(cheshire_request: CheshireRequest):
    # Extract the text from Cheshire Cat's request
    full_text = cheshire_request.text

    # Split the text into system message and user messages
    parts = full_text.split("Human: ")
    system_message = parts[0].strip()
    user_messages = [msg.strip() for msg in parts[1:] if msg.strip()]

    system_message = "You are a helpful assistant."

    # Prepare messages for LM Studio
    messages = [{"role": "system", "content": system_message}]
    for msg in user_messages:
        messages.append({"role": "user", "content": msg})

    # Prepare the request for LM Studio
    lm_studio_data = {
        "model": "TheBloke/Llama-2-7B-Chat-GGUF",  # Adjust as needed
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LM_STUDIO_URL, json=lm_studio_data, timeout=None
            )
            response.raise_for_status()
            lm_studio_result = response.json()
            generated_text = lm_studio_result["choices"][0]["message"]["content"]
            if not generated_text:
                generated_text = ""

        logger.info(f"Generated text: {generated_text}")
        return CheshireResponse(text=generated_text)
    except httpx.HTTPError as e:
        logger.error(f"Error communicating with LM Studio: {str(e)}")
        return CheshireResponse(text="Error communicating with LM Studio")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT)
