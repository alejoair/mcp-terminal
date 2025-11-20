# Terminal API Testing Examples

This document provides examples of how to test the Terminal API endpoints.

## Prerequisites

Start the server:
```bash
uvicorn mcp_open_client.api.main:app --host 127.0.0.1 --port 8001
```

## API Endpoints

### 1. Create Terminal

```bash
curl -X POST http://localhost:8001/terminals/ \
  -H "Content-Type: application/json" \
  -d '{"rows": 24, "cols": 80}'
```

Response:
```json
{
  "success": true,
  "terminal_id": "uuid-here",
  "message": "Terminal created successfully"
}
```

### 2. List Terminals

```bash
curl http://localhost:8001/terminals/
```

Response:
```json
{
  "success": true,
  "terminals": [
    {
      "id": "uuid-here",
      "rows": 24,
      "cols": 80,
      "is_alive": true,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "count": 1
}
```

### 3. Send Command to Terminal

```bash
# Send 'ls' command (note: add \n for Enter)
curl -X POST http://localhost:8001/terminals/{terminal_id}/input \
  -H "Content-Type: application/json" \
  -d '{"data": "ls\n"}'
```

### 4. Get Terminal Snapshot

```bash
curl http://localhost:8001/terminals/{terminal_id}/snapshot
```

Response:
```json
{
  "terminal_id": "uuid-here",
  "display": "user@host:~$ ls\nfile1.txt file2.txt\nuser@host:~$ ",
  "lines": ["user@host:~$ ls", "file1.txt file2.txt", "user@host:~$ "],
  "cursor": {"row": 2, "col": 14},
  "size": {"rows": 24, "cols": 80},
  "is_alive": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### 5. Resize Terminal

```bash
curl -X PUT http://localhost:8001/terminals/{terminal_id}/resize \
  -H "Content-Type: application/json" \
  -d '{"rows": 30, "cols": 100}'
```

### 6. Close Terminal

```bash
curl -X DELETE http://localhost:8001/terminals/{terminal_id}
```

## Testing Interactive Commands

### Example 1: Basic Commands

```bash
# 1. Create terminal
TERM_ID=$(curl -s -X POST http://localhost:8001/terminals/ \
  -H "Content-Type: application/json" \
  -d '{"rows": 24, "cols": 80}' | jq -r '.terminal_id')

# 2. Send pwd command
curl -X POST http://localhost:8001/terminals/$TERM_ID/input \
  -H "Content-Type: application/json" \
  -d '{"data": "pwd\n"}'

# 3. Wait a moment
sleep 1

# 4. Get snapshot
curl http://localhost:8001/terminals/$TERM_ID/snapshot | jq '.display'
```

### Example 2: Navigating with vim/nano

For interactive editors like vim or nano, you can send special characters:

```bash
# Start nano
curl -X POST http://localhost:8001/terminals/$TERM_ID/input \
  -H "Content-Type: application/json" \
  -d '{"data": "nano test.txt\n"}'

# Type some text
curl -X POST http://localhost:8001/terminals/$TERM_ID/input \
  -H "Content-Type: application/json" \
  -d '{"data": "Hello World"}'

# Send Ctrl+X (exit)
curl -X POST http://localhost:8001/terminals/$TERM_ID/input \
  -H "Content-Type: application/json" \
  -d '{"data": "\u0018"}'

# Send Y (yes to save)
curl -X POST http://localhost:8001/terminals/$TERM_ID/input \
  -H "Content-Type: application/json" \
  -d '{"data": "y"}'

# Send Enter (confirm filename)
curl -X POST http://localhost:8001/terminals/$TERM_ID/input \
  -H "Content-Type: application/json" \
  -d '{"data": "\n"}'
```

### Special Characters

Common control characters for terminal interaction:
- Enter: `\n`
- Ctrl+C: `\u0003`
- Ctrl+D: `\u0004`
- Ctrl+X: `\u0018`
- Ctrl+Z: `\u001A`
- Escape: `\u001B`
- Tab: `\t`
- Backspace: `\u007F`

## Using with LLM/MCP Tools

The terminal endpoints are automatically exposed as MCP tools via fastapi-mcp:

- `mcp_create_terminal`
- `mcp_list_terminals`
- `mcp_get_terminal_snapshot`
- `mcp_send_terminal_input`
- `mcp_resize_terminal`
- `mcp_close_terminal`

An LLM can use these tools to:
1. Create a terminal session
2. Run commands and observe output
3. Navigate interactive programs
4. Parse command results
5. Close terminal when done
