import httpx
from fastapi import FastAPI
import os

app = FastAPI()

# La IP del NLB que creaste en IBM Cloud
PROXY_URL = "http://10.240.1.5/empleados.json"

@app.get("/data")
async def get_data():
    async with httpx.AsyncClient() as client:
        # Code Engine llama a la VSI a través del NLB
        response = await client.get(PROXY_URL)
        return response.json()

@app.get("/version")
def version():
    return {"version": "final definitiva sin cambios 3"}