import httpx
from fastapi import FastAPI
import os
import socket

app = FastAPI()

# Mantenemos tu IP confirmada
PROXY_URL = "http://192.168.1.29/empleados.json"

@app.get("/data")
async def get_data():
    # 1. Aumentamos el timeout. httpx por defecto es muy estricto (5s).
    # En entornos de VPC a veces la primera conexión tarda un poco más.
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(PROXY_URL)
            response.raise_for_status() # Lanza error si el NLB devuelve 4xx o 5xx
            return response.json()
        except Exception as e:
            return {"error": f"Error conectando a la VSI: {str(e)}"}

@app.get("/test")
def test_connect():
    """Prueba de conectividad TCP directa"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5) # 5 segundos es más realista para una red privada
    try:
        s.connect(("192.168.1.29", 80))
        return {"status": "CONECTADO AL VPE", "ip": "192.168.1.29", "port": 80}
    except Exception as e:
        return {"status": "BLOQUEADO", "error": str(e)}
    finally:
        s.close()

@app.get("/version")
def version():
    # He añadido el puerto para que siempre recuerdes por dónde entras
    return {"version": "final definitiva v4", "target": "NLB-Port-80"}