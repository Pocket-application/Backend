import hmac
import hashlib
import json
from core.settings import settings

LOG_SIGNING_KEY = settings.log_signing_key


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
