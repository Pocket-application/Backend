![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)

# 💰 API de Finanzas Personales

API REST desarrollada con **FastAPI** para la gestión de finanzas personales.
Permite a los usuarios administrar cuentas, categorías, movimientos financieros,
transferencias entre cuentas, auditoría y consulta de saldos.

---

## 🧱 Arquitectura General

La API está diseñada bajo una arquitectura **modular y segura**, con los siguientes principios:

- Autenticación basada en **JWT (access + refresh tokens)**
- **Auditoría centralizada** de todas las peticiones
- **Rate limiting** a nivel de middleware
- Lógica crítica de saldos delegada a **funciones SQL en PostgreSQL**
- Separación clara entre:
  - Routers (API)
  - Services (lógica de negocio)
  - Repositories (acceso a datos)
  - Models (ORM)
  - Schemas (Pydantic)

---

## 🔐 Autenticación

### Login
`POST /auth/login`

Genera:
- `access_token` (JWT corto)
- `refresh_token` (persistido en BD)

Todos los endpoints protegidos requieren:

```
Authorization: Bearer <access_token>
```

---

## 👤 Usuarios

### Registrar usuario (público)
`POST /usuarios`

### Actualizar datos del usuario
- `PUT /usuarios/nombre`
- `PUT /usuarios/correo`
- `PUT /usuarios/telefono`
- `PUT /usuarios/password`

---

## 🏦 Cuentas

### Crear cuenta
`POST /cuentas`

### Listar cuentas
`GET /cuentas`

### Actualizar cuenta
`PUT /cuentas/{cuenta_id}`

### Eliminar cuenta
`DELETE /cuentas/{cuenta_id}`

---

## 🏷️ Categorías

### Crear categoría
`POST /categorias`

### Listar categorías
`GET /categorias`

### Actualizar categoría
`PUT /categorias/{categoria_id}`

### Eliminar categoría
`DELETE /categorias/{categoria_id}`

---

## 📊 Flujo (Movimientos)

Los movimientos representan ingresos y egresos reales.

### Crear movimiento
`POST /flujo`

### Listar movimientos
`GET /flujo`

### Actualizar movimiento
`PUT /flujo/{movimiento_id}`

### Eliminar movimiento
`DELETE /flujo/{movimiento_id}`

### Reglas importantes
- Ingreso → `tipo_egreso = NULL`
- Egreso → `tipo_egreso = Fijo | Variable`
- Las reglas se validan a nivel **BD y backend**

---

## 🔁 Transferencias

Una transferencia genera automáticamente **dos movimientos**:
- 🔴 Egreso (cuenta origen)
- 🟢 Ingreso (cuenta destino)

### Crear transferencia
`POST /transferencias`

### Listar transferencias
`GET /transferencias`

### Obtener transferencia
`GET /transferencias/{id}`

### Actualizar transferencia
`PUT /transferencias/{id}`  
(Sincroniza automáticamente los movimientos asociados)

### Eliminar transferencia
`DELETE /transferencias/{id}`  
(Elimina también los flujos relacionados)

---

## 💹 Saldos

Los saldos se calculan mediante **funciones SQL optimizadas**.

### Saldo por cuenta
`GET /saldos/cuentas`

### Saldo por rango de fechas
`GET /saldos/rango?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD`

### Reajuste de saldo
`POST /saldos/reajuste`

---

## 🧾 Auditoría

Todas las peticiones pasan por un **middleware de auditoría** que registra:

- Usuario
- IP
- Ruta
- Método
- Status code
- Duración
- Body (cuando aplica)
- Firma criptográfica encadenada

Esto permite:
- Trazabilidad completa
- Detección de alteraciones
- Cumplimiento y seguridad

---

## 🚦 Rate Limiting

Implementado en middleware (sin Redis):

- Por IP + método + ruta
- Reglas específicas por endpoint
- Protección contra:
  - Fuerza bruta
  - DDoS básico
  - Abuso de endpoints críticos

---

## 🗄️ Base de Datos

- PostgreSQL
- Uso de:
  - Constraints fuertes
  - Índices optimizados
  - Funciones SQL para cálculos
  - Relaciones consistentes

---

## 📦 Tecnologías

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT
- Python 3.11+

---

## 🚀 Estado del Proyecto

✔ Autenticación  
✔ Auditoría  
✔ Finanzas completas  
✔ Transferencias consistentes  
✔ Rate limit  
✔ Documentación clara  

Proyecto listo para:
- Frontend web / móvil
- Escalado con Redis
- Despliegue productivo

---

## 🧠 Cache con Redis

Este proyecto utiliza Redis como sistema de cache para optimizar el rendimiento de los endpoints de lectura más costosos, reduciendo la carga sobre la base de datos y mejorando los tiempos de respuesta del API.

La cache se aplica exclusivamente en operaciones de lectura (GET) y se invalida automáticamente ante cualquier operación de escritura que pueda afectar los datos.

### 🏗️ Arquitectura de Cache

* Backend: FastAPI
* Cache: Redis
* Cliente Redis: ``redis-py`` en modo asíncrono
* Estrategia: Cache por usuario (multi-tenant safe)
* TTL por defecto: 5 minutos
```bash
Cliente → FastAPI → Redis (hit) → Response
                  ↓ (miss)
               PostgreSQL → Redis → Response
```
### 🔐 Principios de Diseño
* ✅ Cache solo para lectura
* ❌ Nunca cachear escritura
* 🔄 Invalidación agresiva
* 🧩 Keys segmentadas por usuario
* 🚀 Fallback automático a DB

### 🧩 Estructura de Keys

Las claves de Redis siguen una estructura clara y consistente:

#### Saldos
```bash
saldos:cuentas:{user_id}
saldos:rango:{user_id}:{fecha_inicio}:{fecha_fin}
```
#### Flujos
```bash
flujo:list:{user_id}
```

#### Transferencias
```bash
transferencias:list:{user_id}
transferencias:detail:{user_id}:{transferencia_id}
```

### 🧨 Estrategia de Invalidación

Cualquier operación que modifique datos financieros invalida automáticamente:
* Cache de saldos
* Cache de flujos
* Cache de transferencias

Ejemplo:
```py
await cache_delete_pattern(f"saldos:*:{user.id}*")
await cache_delete_pattern(f"flujo:list:{user.id}")
await cache_delete_pattern(f"transferencias:*:{user.id}*")
```

Esto garantiza consistencia total sin necesidad de lógica compleja.
---

## 📄 Licencia

Este proyecto está licenciado bajo la **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

### ❌ Uso comercial prohibido
No está permitido:
- Usar este proyecto en productos pagos
- Ofrecerlo como SaaS
- Integrarlo en soluciones comerciales
- Venderlo total o parcialmente

### ✅ Uso permitido
- Uso personal
- Uso educativo
- Portafolio
- Estudio y aprendizaje
- Modificaciones sin fines comerciales

Para usos comerciales, contactar al autor.