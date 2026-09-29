import http.server
import socketserver
import os
import json
import threading

PORT = 8080
STATE_FILE = "store_state.json"
lock = threading.Lock()

class KiranaHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for mobile devices
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/sync'):
            with lock:
                if os.path.exists(STATE_FILE):
                    try:
                        with open(STATE_FILE, 'r', encoding='utf-8') as f:
                            data = f.read()
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(data.encode('utf-8'))
                        return
                    except Exception as e:
                        pass
            # Default empty if no state yet
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'{"exists": false}')
            return
        
        # Fallback to standard static file serving
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/sync'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                parsed = json.loads(body)
                with lock:
                    with open(STATE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(parsed, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'{"success": true}')
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), KiranaHandler) as httpd:
        print(f"Room No 114 Kirana Server running on port {PORT} with Live Multi-Device Sync (/api/sync)")
        httpd.serve_forever()
