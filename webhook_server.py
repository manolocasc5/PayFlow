#!/usr/bin/env python3
"""
Servidor webhook de prueba para el hook HTTP de PayFlow.
Ejecutar con: python webhook_server.py
Escucha en http://localhost:5001
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import json


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"raw": body.decode()}

        event = data.get("hook_event_name", "unknown")
        session = data.get("session_id", "unknown")[:8]
        auth = self.headers.get("Authorization", "none")
        last_msg = data.get("last_assistant_message", "")
        preview = last_msg[:120] + "..." if len(last_msg) > 120 else last_msg

        print(f"\n{'='*60}")
        print(f"  WEBHOOK RECIBIDO — {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"  Evento:  {event}")
        print(f"  Sesión:  {session}...")
        print(f"  Auth:    {auth[:30]}...")
        print(f"  Preview: {preview}")
        print(f"{'='*60}\n")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP estándar


if __name__ == "__main__":
    server = HTTPServer(("localhost", 5001), WebhookHandler)
    print("Webhook server escuchando en http://localhost:5001")
    print("Esperando notificaciones de Claude Code...\n")
    server.serve_forever()