## =========================================================
## main.py - Versión Final con Fix de Firma para Private Path
## =========================================================

from sys import api_version
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

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ce-cos-debug")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_cos_client():
    # Extraemos las llaves HMAC
    access_key = os.environ.get("COS_API_KEY") # Aquí ahora va el access_key_id
    secret_key = os.environ.get("COS_AUTH_SECRET") # El secret_access_key
    endpoint = os.environ.get("COS_ENDPOINT")
    instance_id = os.environ.get("COS_INSTANCE_CRN")

    client = ibm_boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        ibm_service_instance_id=instance_id,
        endpoint_url=endpoint,
        verify=False,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"}
        )
    )

    # El fix del Host para engañar al COS a través del proxy
    def fix_hostname(request, **kwargs):
        request.headers['Host'] = 's3.direct.eu-de.cloud-object-storage.appdomain.cloud'

    client.meta.events.register('before-sign.s3', fix_hostname)
    
    return client

# =========================
# LÓGICA DE DATOS
# =========================
def get_empleados_data():
    client = get_cos_client()
    bucket = os.environ["COS_BUCKET"]
    key = "empleados.json"

    try:
        logger.info(f"📦 Leyendo {key} desde el bucket {bucket}")
        response = client.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()
        return json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.error(f"💥 Error al acceder al COS: {str(e)}")
        raise e

# =========================
# ENDPOINTS
# =========================
@app.get("/empleados")
def get_empleados(
    depto:  Optional[str] = Query(None),
    cargo:  Optional[str] = Query(None),
    ciudad: Optional[str] = Query(None),
):
    data = get_empleados_data()

    if depto: data = [e for e in data if e["depto"] == depto]
    if cargo: data = [e for e in data if e["cargo"] == cargo]
    if ciudad: data = [e for e in data if e["ciudad"] == ciudad]

    return data

@app.get("/info")
def get_info():
    endpoint = os.environ.get("COS_ENDPOINT", "no configurado")
    return {
        "endpoint": endpoint,
        "vpe_private_path": "192.168.1.12",
        "proxy_vsi_vpe": "192.168.1.18",
        "status": "Final Version"
    }

@app.get("/version")
def version():
    return {"version": "4.0.0-fixed-headers"
}