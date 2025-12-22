from log_signer import sign_log


def verify_log(log_data: dict, firma_guardada: str, firma_anterior: str | None) -> bool:
    firma_calculada = sign_log(log_data, firma_anterior)
    return firma_calculada == firma_guardada
