import httpx
from fastapi import FastAPI
import os
import socket

app = FastAPI()

# Mantenemos tu IP confirmada
PROXY_URL = "http://service.endpoint.presentation.corp/empleados.json"

@app.get("/data")
async def get_data():
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            response = await client.get(PROXY_URL)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Más detalle del error
            return {
                "error": str(e),
                "tipo": type(e).__name__,
                "detalle": repr(e)
            }

@app.get("/version")
def version():
    # He añadido el puerto para que siempre recuerdes por dónde entras
    return {"version": "final definitiva v7", "target": "NLB-Port-80"}