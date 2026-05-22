from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.client import Config
import json
import os
import logging
from typing import Optional

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ce-cos-debug")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_cos_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("COS_API_KEY"),
        aws_secret_access_key=os.environ.get("COS_AUTH_SECRET"),
        endpoint_url=os.environ.get("COS_ENDPOINT"),
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"}
        ),
        verify=False,
        region_name="eu-de"
    )

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
        "status": "boto3-hmac"
    }

@app.get("/version")
def version():
    return {"version": "5.0.0-boto3-hmac"}