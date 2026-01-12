# =========================
# Base image
# =========================
FROM ubuntu:22.04

# =========================
# Variables de entorno
# =========================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# =========================
# Instalar dependencias del sistema
# =========================
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =========================
# Directorio de trabajo
# =========================
WORKDIR /app

# =========================
# Copiar requirements primero (mejor cache)
# =========================
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

# =========================
# Copiar el resto del proyecto
# =========================
COPY . .

# =========================
# Exponer puerto
# =========================
EXPOSE 8000

# =========================
# Comando de arranque
# =========================
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
