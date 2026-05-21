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
        verify=False,
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
    import socket
    endpoint = os.environ.get("COS_ENDPOINT", "no configurado")
    vpe_ip = "192.168.1.18"

    # Extraer hostname del endpoint
    hostname = endpoint.replace("https://", "").replace("http://", "").split("/")[0]

    # Resolver DNS
    try:
        resolved_ips = list(set(r[4][0] for r in socket.getaddrinfo(hostname, None)))
    except Exception as e:
        resolved_ips = [f"Error resolviendo DNS: {str(e)}"]

    usa_vpe = vpe_ip in resolved_ips

    return {
        "servicio": "Cloud Object Storage",
        "endpoint": endpoint,
        "hostname": hostname,
        "ips_resueltas": resolved_ips,
        "vpe_ip_esperada": vpe_ip,
        "usa_vpe_exacto": usa_vpe,
        "bucket": os.environ.get("COS_BUCKET", "no configurado"),
        "tipo_conexion": f"VPE exacto ({vpe_ip})" if usa_vpe else "Red privada IBM (sin VPE específico)",
    }

@app.get("/test-vpe")
def test_vpe():
    import socket
    import requests
    
    vpe_ip = "192.168.1.18"
    vsi_ip = "192.168.1.12" # La IP de tu NLB/VSI
    
    results = {}
    
    # 1. Probar conexión a la VSI (NLB)
    try:
        s = socket.create_connection((vsi_ip, 80), timeout=3)
        results["conexion_vsi_80"] = "EXITOSA"
        s.close()
    except Exception as e:
        results["conexion_vsi_80"] = f"FALLIDA: {str(e)}"

    # 2. Probar conexión al VPE desde Code Engine (por si acaso)
    try:
        s = socket.create_connection((vpe_ip, 443), timeout=3)
        results["conexion_vpe_443"] = "EXITOSA"
        s.close()
    except Exception as e:
        results["conexion_vpe_443"] = f"FALLIDA: {str(e)}"

    return results

@app.get("/filtros")
def get_filtros():
    data = get_empleados_data()
    return {
        "depto":  sorted(set(e["depto"]  for e in data)),
        "cargo":  sorted(set(e["cargo"]  for e in data)),
        "ciudad": sorted(set(e["ciudad"] for e in data)),
    }
