"""SSL 憑證解析模組"""

from __future__ import annotations

import ssl
import socket
from datetime import datetime, timezone
from typing import Any

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID, NameOID


def _get_cert_pem(hostname: str, port: int = 443, timeout: int = 10) -> bytes:
    ctx = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert_der = ssock.getpeercert(binary_form=True)
    return cert_der


def _parse_name(name: x509.Name) -> dict[str, str]:
    result = {}
    for attr in name:
        oid = attr.oid
        if oid == NameOID.COMMON_NAME:
            result["CN"] = attr.value
        elif oid == NameOID.ORGANIZATION_NAME:
            result["O"] = attr.value
        elif oid == NameOID.COUNTRY_NAME:
            result["C"] = attr.value
        elif oid == NameOID.LOCALITY_NAME:
            result["L"] = attr.value
        elif oid == NameOID.STATE_OR_PROVINCE_NAME:
            result["ST"] = attr.value
    return result


def query_ssl(hostname: str, port: int = 443) -> dict[str, Any]:
    """查詢 SSL 憑證資訊"""
    hostname = hostname.strip().removeprefix("https://").removeprefix("http://").split("/")[0]
    try:
        cert_der = _get_cert_pem(hostname, port)
        cert = x509.load_der_x509_certificate(cert_der, default_backend())

        now = datetime.now(timezone.utc)
        not_before = cert.not_valid_before_utc
        not_after = cert.not_valid_after_utc
        days_left = (not_after - now).days

        # SAN
        san_list: list[str] = []
        try:
            san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            san_list = [str(n.value) for n in san_ext.value]
        except x509.ExtensionNotFound:
            pass

        # 憑證鏈（基本資訊，單連線只取葉憑證）
        return {
            "hostname": hostname,
            "port": port,
            "subject": _parse_name(cert.subject),
            "issuer": _parse_name(cert.issuer),
            "serial_number": hex(cert.serial_number),
            "not_before": not_before.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "not_after": not_after.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "days_left": days_left,
            "san": san_list,
            "signature_algorithm": cert.signature_algorithm_oid.dotted_string,
            "version": cert.version.name,
            "is_expired": days_left < 0,
            "is_expiring_soon": 0 <= days_left <= 30,
        }
    except ssl.SSLCertVerificationError as e:
        return {"hostname": hostname, "error": f"SSL 驗證失敗：{e}"}
    except ConnectionRefusedError:
        return {"hostname": hostname, "error": f"連線被拒絕（{hostname}:{port}）"}
    except socket.timeout:
        return {"hostname": hostname, "error": "連線超時"}
    except Exception as e:
        return {"hostname": hostname, "error": str(e)}
