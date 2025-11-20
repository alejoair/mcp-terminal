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