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
    # Estas son las variables que YA TIENES
    api_key = os.environ.get("COS_API_KEY")
    service_instance_id = os.environ.get("COS_INSTANCE_CRN")
    endpoint = os.environ.get("COS_ENDPOINT")

    # Creamos el cliente inyectando la API KEY en los campos de AWS 
    # para que el firmante de S3 tenga un string (tu clave) y no un None
    client = ibm_boto3.client(
        "s3",
        aws_access_key_id=api_key,       # Usamos tu API KEY aquí
        aws_secret_access_key=api_key,   # Y aquí
        ibm_api_key_id=api_key,          # Y aquí (el estándar de IBM)
        ibm_service_instance_id=service_instance_id,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"}
        ),
        verify=False, 
        endpoint_url=endpoint,
    )

    # El fix del Host sigue siendo necesario para que Nginx pase la bola al COS
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