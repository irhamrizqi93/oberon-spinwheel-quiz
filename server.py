#!/usr/bin/env python3
"""Oberon Spinwheel Quiz Server — simpan hasil ke JSON + layani quiz."""
import json, os, time, http.server, urllib.parse, sys
from pathlib import Path

PORT = int(os.environ.get("PORT", 8765))
DATA_DIR = Path(__file__).parent
RESULTS_FILE = DATA_DIR / "results.json"

# Load/save helpers
def load_results():
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    return []

def save_results(entries):
    RESULTS_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2))

class QuizHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silent

    def serve_static(self, path):
        try:
            file_path = DATA_DIR / path.lstrip("/")
            if file_path.suffix == ".html":
                content = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content)
            elif file_path.suffix == ".json":
                content = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_static("/index.html")
        elif self.path == "/results.json":
            self.serve_static("/results.json")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/submit":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)

            entry = {
                "nama": data.get("nama", "Tanpa Nama"),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S WIB"),
                "score": data.get("score", 0),
                "total": data.get("total", 10),
                "confidence": data.get("confidence", 0),
                "pertanyaan": data.get("pertanyaan", ""),
                "answers": data.get("answers", []),
            }

            results = load_results()
            results.append(entry)
            save_results(results)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "id": len(results)}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    addr = ("0.0.0.0", PORT)
    server = http.server.HTTPServer(addr, QuizHandler)
    print(f"Quiz server running on port {PORT}")
    server.serve_forever()
