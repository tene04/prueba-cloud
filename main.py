import httpx
from fastapi import FastAPI
import os
import socket

app = FastAPI()

# Mantenemos tu IP confirmada
PROXY_URL = "http://192.160.0.4/empleados.json"

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

@app.get("/test")
def test_connect():
    """Prueba de conectividad TCP directa"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5) # 5 segundos es más realista para una red privada
    try:
        s.connect(("192.160.0.4", 80))
        return {"status": "CONECTADO AL VPE", "ip": "192.160.0.4", "port": 80}
    except Exception as e:
        return {"status": "BLOQUEADO", "error": str(e)}
    finally:
        s.close()

@app.get("/version")
def version():
    # He añadido el puerto para que siempre recuerdes por dónde entras
    return {"version": "final definitiva v6", "target": "NLB-Port-80"}