"""Send Python to the open Blender through the Blender MCP add-on's local bridge.
Usage: python bl.py script.py   (script sets `result` to return a value)"""
import json, socket, sys
code = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
s = socket.create_connection(("127.0.0.1", 9876), timeout=10)
s.settimeout(float(sys.argv[2]) if len(sys.argv) > 2 else 300)
s.sendall((json.dumps({"type": "execute", "code": code, "strict_json": False}) + "\0").encode())
buf = b""
while b"\0" not in buf:
    chunk = s.recv(65536)
    if not chunk: break
    buf += chunk
print(json.dumps(json.loads(buf.split(b"\0")[0].decode()), indent=1))
