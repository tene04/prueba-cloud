import httpx
from fastapi import FastAPI
import os

app = FastAPI()

# La IP del NLB que creaste en IBM Cloud
PROXY_URL = "http://192.168.1.29/empleados.json"

@app.get("/data")
async def get_data():
    async with httpx.AsyncClient() as client:
        # Code Engine llama a la VSI a través del NLB
        response = await client.get(PROXY_URL)
        return response.json()

import socket

def test_connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        # Intentamos abrir conexión TCP pura al VPE
        s.connect(("192.168.1.29", 80))
        return "CONECTADO AL VPE"
    except Exception as e:
        return f"BLOQUEADO POR SG DEL VPE: {e}"
    finally:
        s.close()

@app.get("/version")
def version():
    return {"version": "final definitiva sin cambios 4"}