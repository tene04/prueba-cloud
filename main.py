from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import ibm_boto3
from ibm_botocore.client import Config
import json
import os
import socket
import time
import logging
from typing import Optional

app = FastAPI()

# =========================
# LOGGING GLOBAL
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ce-cos-debug")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# COS CLIENT CORREGIDO
# =========================
def get_cos_client():
    endpoint = os.environ.get("COS_ENDPOINT")
    bucket = os.environ.get("COS_BUCKET")

    logger.info("====================================")
    logger.info("🔧 CONFIGURANDO SESIÓN Y CLIENTE COS")
    
    # 1. Creamos una sesión para que la autenticación con IAM 
    # se gestione de forma independiente al endpoint del VPE.
    session = ibm_boto3.session.Session(
        ibm_api_key_id=os.environ["COS_API_KEY"],
        ibm_service_instance_id=os.environ["COS_INSTANCE_CRN"]
    )

    # 2. Creamos el cliente desde la sesión
    client = session.client(
        "s3",
        config=Config(
            signature_version="oauth",
            s3={"addressing_style": "path"}
        ),
        # verify=False es necesario porque el VPE usa certificados internos
        verify=False, 
        endpoint_url=endpoint,
    )

    logger.info(f"✅ Cliente vinculado a: {endpoint}")
    logger.info("====================================")

    return client


# =========================
# COS READ DEBUG
# =========================
def get_empleados_data():
    start = time.time()
    client = get_cos_client()
    bucket = os.environ["COS_BUCKET"]
    key = "empleados.json"

    logger.info("📦 SOLICITANDO OBJETO A TRAVÉS DE VPE")

    try:
        response = client.get_object(
            Bucket=bucket,
            Key=key
        )

        logger.info("📥 RESPUESTA RECIBIDA")
        body = response["Body"].read()
        data = json.loads(body.decode("utf-8"))

        logger.info(f"⏱ Operación completada en {time.time() - start:.2f}s")
        return data

    except Exception as e:
        logger.error(f"💥 ERROR EN COS: {str(e)}")
        raise


# =========================
# ENDPOINTS
# =========================
@app.get("/empleados")
def get_empleados(
    depto:  Optional[str] = Query(None),
    cargo:  Optional[str] = Query(None),
    ciudad: Optional[str] = Query(None),
):
    logger.info("🚀 REQUEST /empleados")
    data = get_empleados_data()

    if depto: data = [e for e in data if e["depto"] == depto]
    if cargo: data = [e for e in data if e["cargo"] == cargo]
    if ciudad: data = [e for e in data if e["ciudad"] == ciudad]

    return data

@app.get("/info")
def get_info():
    endpoint = os.environ.get("COS_ENDPOINT", "no configurado")
    hostname = endpoint.replace("https://", "").replace("http://", "").split("/")[0]
    
    try:
        resolved_ips = list(set(r[4][0] for r in socket.getaddrinfo(hostname, None)))
    except Exception as e:
        resolved_ips = [f"DNS ERROR: {str(e)}"]

    return {
        "endpoint": endpoint,
        "ips_resueltas": resolved_ips,
        "vpe_fijo": "192.168.1.18",
        "proxy_vsi": "192.168.1.12"
    }

@app.get("/test-vpe")
def test_vpe():
    results = {}
    vsi_ip, vpe_ip = "192.168.1.12", "192.168.1.18"

    for name, ip, port in [("vsi_80", vsi_ip, 80), ("vpe_443", vpe_ip, 443)]:
        try:
            socket.create_connection((ip, port), timeout=3).close()
            results[name] = "OK"
        except Exception as e:
            results[name] = f"Error: {str(e)}"
    
    return results

@app.get("/version")
def version():
    return {"version": "final-vpe-fix"}