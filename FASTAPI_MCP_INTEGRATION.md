# FastAPI-MCP Integration Guide

Este documento explica cómo se integra fastapi-mcp en el proyecto.

## ¿Qué es FastAPI-MCP?

FastAPI-MCP es una librería que convierte automáticamente endpoints de FastAPI en herramientas MCP (Model Context Protocol) que pueden ser invocadas por LLMs.

## Instalación

```bash
pip install fastapi-mcp
```

## Implementación en main.py

### 1. Importar FastAPI-MCP

```python
from fastapi_mcp import FastApiMCP
```

### 2. Crear la aplicación FastAPI normalmente

```python
from fastapi import FastAPI

app = FastAPI(
    title="MCP Open Client API",
    description="API for managing MCP servers",
    version="0.1.0",
)

# Agregar routers normales
app.include_router(servers_router)
app.include_router(terminal_router)
app.include_router(providers_router)
# ... etc
```

### 3. Montar FastAPI-MCP

```python
# Mount MCP server using fastapi-mcp
try:
    mcp = FastApiMCP(app, name="MCP Open Client API")
    mcp.mount_http()  # Mounts at /mcp by default
    logger.info("MCP server mounted at /mcp endpoint")
except Exception as e:
    logger.warning(f"Failed to mount MCP server: {e}")
```

## Resultado

### Antes (REST API tradicional)

```bash
POST http://localhost:8001/terminals/
GET http://localhost:8001/terminals/
POST http://localhost:8001/terminals/{id}/input
```

### Después (REST API + MCP Tools)

**1. API REST sigue funcionando igual:**
```bash
POST http://localhost:8001/terminals/
GET http://localhost:8001/terminals/
```

**2. Además, se exponen como MCP Tools:**
```
http://localhost:8001/mcp
```

**Herramientas MCP disponibles:**
- `create_terminal_terminals__post`
- `list_terminals_terminals__get`
- `send_terminal_input_terminals__terminal_id__input_post`
- `get_terminal_snapshot_terminals__terminal_id__snapshot_get`
- `resize_terminal_terminals__terminal_id__resize_put`
- `close_terminal_terminals__terminal_id__delete`

## Convención de Nombres

FastAPI-MCP genera nombres de herramientas basados en:
- Nombre de la función del endpoint
- Path del endpoint
- Método HTTP

**Ejemplo:**
```python
@router.post("/terminals/")
async def create_terminal(...):
    pass
```

Se convierte en:
```
create_terminal_terminals__post
```

## Uso desde un LLM

Un LLM puede conectarse al servidor MCP en `/mcp` y descubrir/invocar las herramientas:

```python
# El LLM ve esto:
{
  "tools": [
    {
      "name": "create_terminal_terminals__post",
      "description": "Create a new terminal session",
      "inputSchema": {
        "type": "object",
        "properties": {
          "rows": {"type": "integer", "default": 24},
          "cols": {"type": "integer", "default": 80}
        }
      }
    }
  ]
}
```

## Ventajas

1. **Sin código adicional**: Los endpoints REST se convierten automáticamente en MCP tools
2. **Documentación automática**: Los schemas Pydantic se convierten en inputSchema de MCP
3. **Dos interfaces en uno**: REST API para humanos, MCP para LLMs
4. **Type safety**: Validación de Pydantic funciona para ambos

## Ejemplo de Flujo Completo

### 1. Definir endpoint FastAPI normal

```python
# api/endpoints/terminal.py
from pydantic import BaseModel

class TerminalCreate(BaseModel):
    rows: int = 24
    cols: int = 80

@router.post("/terminals/")
async def create_terminal(request: TerminalCreate):
    terminal_id = await manager.create(request.rows, request.cols)
    return {"success": True, "terminal_id": terminal_id}
```

### 2. Montar fastapi-mcp en main.py

```python
# api/main.py
from fastapi_mcp import FastApiMCP

app.include_router(terminal_router)
mcp = FastApiMCP(app, name="My API")
mcp.mount_http()
```

### 3. LLM invoca la herramienta

```python
# El LLM hace:
tool_call = {
    "name": "create_terminal_terminals__post",
    "arguments": {"rows": 30, "cols": 100}
}

# Que se traduce internamente a:
POST http://localhost:8001/terminals/
Content-Type: application/json
{"rows": 30, "cols": 100}

# Y retorna:
{"success": true, "terminal_id": "uuid-here"}
```

## Configuración Adicional

### Personalizar path de montaje

```python
mcp.mount_http(path="/my-mcp-endpoint")  # Default es /mcp
```

### Filtrar endpoints expuestos

FastAPI-MCP expone TODOS los endpoints por defecto. Para filtrar, usa tags de FastAPI:

```python
# Solo exponer ciertos routers
terminal_router = APIRouter(prefix="/terminals", tags=["mcp-exposed"])
internal_router = APIRouter(prefix="/internal", tags=["internal"])
```

## Debugging

Ver herramientas disponibles:
```bash
curl http://localhost:8001/mcp/tools
```

Ver schema de una herramienta:
```bash
curl http://localhost:8001/mcp/tools/create_terminal_terminals__post
```

## Notas Importantes

- FastAPI-MCP es **opcional**: Si no está instalado, el servidor sigue funcionando como API REST normal
- Los endpoints siguen siendo accesibles via REST: `/mcp` es **adicional**, no reemplaza nada
- La validación Pydantic funciona igual para ambas interfaces
- Los errores HTTP se mapean a errores MCP correctamente
