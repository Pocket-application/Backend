import hmac
import hashlib
import json
import os

LOG_SIGNING_KEY = os.environ["LOG_SIGNING_KEY"]


def sign_log(data: dict, firma_anterior: str | None) -> str:
    """
    Firma HMAC SHA256 con hash encadenado
    """
    payload = {
        "data": data,
        "firma_anterior": firma_anterior
    }

    message = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()

    return hmac.new(
        LOG_SIGNING_KEY.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
