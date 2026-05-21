from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import ibm_boto3
from ibm_botocore.client import Config

import json
import os
import socket
import time
import logging

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
# COS CLIENT DEBUG
# =========================
def get_cos_client():
    endpoint = os.environ.get("COS_ENDPOINT")
    bucket = os.environ.get("COS_BUCKET")

    logger.info("====================================")
    logger.info("🔧 CREANDO CLIENTE COS")
    logger.info(f"Endpoint: {endpoint}")
    logger.info(f"Bucket: {bucket}")
    logger.info(f"Instance CRN: {'COS_INSTANCE_CRN' in os.environ}")
    logger.info(f"API KEY: {'COS_API_KEY' in os.environ}")

    client = ibm_boto3.client(
        "s3",
        ibm_api_key_id=os.environ["COS_API_KEY"],
        ibm_service_instance_id=os.environ["COS_INSTANCE_CRN"],
        config=Config(
            signature_version="oauth",
            s3={"addressing_style": "path"}
        ),
        verify=False,
        endpoint_url=endpoint,
    )

    logger.info("✅ Cliente COS creado correctamente")
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

    logger.info("📦 INICIO GET_OBJECT")
    logger.info(f"Bucket: {bucket}")
    logger.info(f"Key: {key}")

    try:
        response = client.get_object(
            Bucket=bucket,
            Key=key
        )

        logger.info("📥 RESPUESTA RECIBIDA DE COS")

        body = response["Body"].read()
        size = len(body)

        logger.info(f"📏 Tamaño payload: {size} bytes")

        data = json.loads(body.decode("utf-8"))

        logger.info(f"⏱ COS OK en {time.time() - start:.2f}s")
        logger.info("====================================")

        return data

    except Exception as e:
        logger.error("💥 ERROR EN GET_OBJECT COS")
        logger.error(str(e))
        logger.error("====================================")
        raise


# =========================
# ENDPOINT PRINCIPAL
# =========================
@app.get("/empleados")
def get_empleados(
    depto:  str = Query(None),
    cargo:  str = Query(None),
    ciudad: str = Query(None),
):

    logger.info("🚀 REQUEST /empleados")

    data = get_empleados_data()

    if depto:
        logger.info(f"🔎 filtro depto={depto}")
        data = [e for e in data if e["depto"] == depto]

    if cargo:
        logger.info(f"🔎 filtro cargo={cargo}")
        data = [e for e in data if e["cargo"] == cargo]

    if ciudad:
        logger.info(f"🔎 filtro ciudad={ciudad}")
        data = [e for e in data if e["ciudad"] == ciudad]

    logger.info(f"📤 respuesta final {len(data)} registros")

    return data


# =========================
# INFO VPE + DNS DEBUG
# =========================
@app.get("/info")
def get_info():

    endpoint = os.environ.get("COS_ENDPOINT", "no configurado")
    hostname = endpoint.replace("https://", "").replace("http://", "").split("/")[0]

    logger.info("🌐 RESOLVIENDO DNS")
    logger.info(f"Hostname: {hostname}")

    try:
        resolved_ips = list(set(
            r[4][0] for r in socket.getaddrinfo(hostname, None)
        ))
    except Exception as e:
        resolved_ips = [f"DNS ERROR: {str(e)}"]

    logger.info(f"IPs: {resolved_ips}")

    return {
        "endpoint": endpoint,
        "hostname": hostname,
        "ips_resueltas": resolved_ips,
        "bucket": os.environ.get("COS_BUCKET"),
    }


# =========================
# TEST DE RED (VSI + VPE)
# =========================
@app.get("/test-vpe")
def test_vpe():

    results = {}

    vsi_ip = "192.168.1.12"
    vpe_ip = "192.168.1.18"

    logger.info("🔌 TEST CONECTIVIDAD")

    # VSI
    try:
        socket.create_connection((vsi_ip, 80), timeout=3).close()
        results["vsi_80"] = "OK"
        logger.info("✔ VSI OK")
    except Exception as e:
        results["vsi_80"] = str(e)
        logger.error(f"❌ VSI FAIL: {e}")

    # VPE
    try:
        socket.create_connection((vpe_ip, 443), timeout=3).close()
        results["vpe_443"] = "OK"
        logger.info("✔ VPE OK")
    except Exception as e:
        results["vpe_443"] = str(e)
        logger.error(f"❌ VPE FAIL: {e}")

    return results


# =========================
@app.get("/version")
def version():
    return {"version": "debug-1.0"}