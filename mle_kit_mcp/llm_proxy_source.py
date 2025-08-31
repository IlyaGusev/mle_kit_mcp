import os

import fire  # type: ignore
import uvicorn
from openai import AsyncOpenAI
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

app = FastAPI()
client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def _check_auth(request: Request) -> None:
    auth = request.headers.get("authorization", "")
    if not ACCESS_TOKEN or auth != f"Bearer {ACCESS_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter key not configured")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    _check_auth(request)
    payload = await request.json()
    if isinstance(payload, dict) and payload.get("stream"):
        payload.pop("stream", None)

    try:
        resp = await client.chat.completions.create(**payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return JSONResponse(resp.model_dump())


@app.get("/health")
async def health() -> JSONResponse:
    if not OPENROUTER_API_KEY:
        return JSONResponse({"error": "missing OPENROUTER_API_KEY"}, 500)
    return JSONResponse({"result": "ok"})


def main(host: str = "127.0.0.1", port: int = 8001) -> None:
    uvicorn.run("llm_proxy:app", host=host, port=port)


if __name__ == "__main__":
    fire.Fire(main)
