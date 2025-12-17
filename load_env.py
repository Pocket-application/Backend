import os

def load_env_file(filepath=".env"):
    """
    Carga variables de entorno desde un archivo `.env` de manera estricta.

    Lee línea por línea el archivo especificado y carga cada par `CLAVE=VALOR` en
    `os.environ`. Si el archivo no existe o contiene líneas inválidas, se lanzará
    una excepción.

    Args:
        filepath (str, optional): Ruta al archivo `.env`. Por defecto `.env`.

    Raises:
        FileNotFoundError: Si no se encuentra el archivo especificado.
        ValueError: Si alguna línea no contiene un formato válido `CLAVE=VALOR`.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo {filepath}. Debes crearlo antes de iniciar la app.")
    
    with open(filepath) as f:
        for line in f:
            if line.strip() == "" or line.strip().startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"Línea inválida en {filepath}: {line.strip()}")
            key, value = line.strip().split("=", 1)
            os.environ[key] = value  # sobrescribimos siempre, no usamos setdefault