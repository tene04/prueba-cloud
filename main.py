from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import ibm_boto3
from ibm_botocore.client import Config
import json
import os
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_cos_client():
    return ibm_boto3.client(
        "s3",
        ibm_api_key_id=os.environ["COS_API_KEY"],
        ibm_service_instance_id=os.environ["COS_INSTANCE_CRN"],
        config=Config(signature_version="oauth"),
        endpoint_url=os.environ["COS_ENDPOINT"],
    )

def get_empleados_data():
    client = get_cos_client()
    response = client.get_object(
        Bucket=os.environ["COS_BUCKET"],
        Key="empleados.json"
    )
    return json.loads(response["Body"].read().decode("utf-8"))

@app.get("/empleados")
def get_empleados(
    depto:  Optional[str] = Query(None),
    cargo:  Optional[str] = Query(None),
    ciudad: Optional[str] = Query(None),
):
    data = get_empleados_data()

    if depto:
        data = [e for e in data if e["depto"] == depto]
    if cargo:
        data = [e for e in data if e["cargo"] == cargo]
    if ciudad:
        data = [e for e in data if e["ciudad"] == ciudad]

    return data

@app.get("/info")
def get_info():
    """Muestra información sobre la configuración de la conexión."""
    endpoint = os.environ.get("COS_ENDPOINT", "no configurado")
    es_vpe = "direct" in endpoint
    return {
        "servicio": "Cloud Object Storage",
        "endpoint": endpoint,
        "bucket": os.environ.get("COS_BUCKET", "no configurado"),
        "conexion_via_vpe": es_vpe,
        "tipo_conexion": "Red privada (VPE)" if es_vpe else "Internet público",
    }

@app.get("/filtros")
def get_filtros():
    data = get_empleados_data()
    return {
        "depto":  sorted(set(e["depto"]  for e in data)),
        "cargo":  sorted(set(e["cargo"]  for e in data)),
        "ciudad": sorted(set(e["ciudad"] for e in data)),
    }