- ● Arquitectura del Proyecto MCP Terminal

  src/mcp_terminal/
  ├── core/                    # Lógica de negocio
  │   └── terminal/
  │       ├── manager.py       # Gestión de sesiones terminales
  │       ├── session.py       # Sesión terminal individual (pty)
  │       └── buffer.py        # Buffer de pantalla virtual
  │
  ├── api/                     # Capa HTTP/REST
  │   ├── dependencies.py      # ✅ Singleton TerminalManager
  │   ├── lifespan.py          # ✅ Startup/Shutdown hooks
  │   └── endpoints.py         # 🔜 HTTP endpoints (CRUD terminales)
  │
  ├── models/                  # Pydantic schemas
  │   └── terminal.py          # Request/Response models
  │
  └── server.py                # 🔜 FastAPI app + CORS + MCP mount

  Flujo:
  1. server.py → Configura FastAPI + middlewares + monta MCP
  2. endpoints.py → Define rutas HTTP usando TerminalManagerDep
  3. dependencies.py → Provee singleton de TerminalManager
  4. core/terminal/ → Implementa lógica de terminales (pty, buffers)
  5. models/ → Define contratos de API (request/response)

  Patrón: Arquitectura en capas con inyección de dependencias (FastAPI Depends).
- Arquitectura Actual - MCP Terminal

  src/mcp_terminal/
  ├── server.py                   # FastAPI app + CORS + MCP mount (56 líneas)
  ├── api/
  │   ├── dependencies.py         # Singleton TerminalManager + DI
  │   ├── lifespan.py            # Startup/shutdown hooks
  │   └── endpoints.py           # REST + WebSocket (ahora con operation_id)
  ├── core/terminal/
  │   ├── manager.py             # Gestión múltiples terminales + reader interno
  │   ├── session.py             # PTY session individual (terminado)
  │   └── buffer.py              # Buffer visual (pyte) + ANSI parsing
  └── models/
      └── terminal.py            # Pydantic schemas (Request/Response)

  Flujo:
  1. create_terminal → Inicia PTY + reader interno
  2. Reader lee PTY → Actualiza buffer circular (5 snapshots)
  3. get_snapshot → Consulta cache instantáneo
  4. send_input → Escribe al PTY
  5. WebSocket /ws → I/O bidireccional (opcional)

  Patrón: Arquitectura en capas + DI + Event-driven (reader interno automático)

  Ahora voy a verificar y commitear los cambios de operation_id.

● Arquitectura MCP Terminal

  Terminal creado
      ↓
  Reader interno (auto-start) → Lee PTY cada 50ms
      ↓
  Buffer circular (5 snapshots) → Actualizado automáticamente
      ↓
  REST API (consulta cache) + WebSocket (streaming opcional)

  Componentes:

  - server.py - FastAPI + MCP mount
  - api/endpoints.py - 6 endpoints REST + 1 WebSocket
  - api/dependencies.py - Singleton TerminalManager
  - core/terminal/manager.py - Coordina sessions + buffers + readers
  - core/terminal/session.py - PTY wrapper (terminado)
  - core/terminal/buffer.py - Screen buffer (pyte)

  API:
  - create_terminal - Crea PTY + inicia reader
  - get_terminal_snapshot - Consulta instantánea del cache
  - send_terminal_input - Escribe al PTY
  - resize_terminal - Cambia dimensiones
  - close_terminal - Limpia recursos
  - list_terminals - Lista activos

  Stack: FastAPI + terminado (PTY) + pyte (buffer) + asyncio
- Publicar Nueva Versión en PyPI (Resumen Rápido)

  1. Actualizar versión en pyproject.toml:
  version = "0.2.2"  # Incrementar
  2. Limpiar y construir:
  rm -rf dist build *.egg-info src/*.egg-info
  python -m build
  3. Publicar:
  python -m twine upload dist/*
  4. Commit:
  git add pyproject.toml
  git commit -m "Bump version to 0.2.2"
  git push

  Versionado: X.Y.Z
  - X = Major (breaking changes)
  - Y = Minor (nuevas features)
  - Z = Patch (bugfixes)