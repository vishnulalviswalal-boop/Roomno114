import http.server
import socketserver
import os
import json
import threading
import database

PORT = 8080
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
        # API: Sync full state from SQLite
        if self.path.startswith('/api/sync'):
            try:
                with lock:
                    state = database.get_full_state()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(state).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        # API: SQLite Database Statistics
        if self.path.startswith('/api/db/stats'):
            try:
                stats = database.get_stats()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(stats, indent=2).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        # API: Download raw SQLite database backup file
        if self.path.startswith('/api/db/backup'):
            if os.path.exists(database.DB_PATH):
                with open(database.DB_PATH, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/x-sqlite3')
                self.send_header('Content-Disposition', 'attachment; filename="store_backup.db"')
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        # Fallback to standard static file serving (index.html, assets, etc.)
        return super().do_GET()

    def do_POST(self):
        # API: Sync full state to SQLite
        if self.path.startswith('/api/sync'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                parsed = json.loads(body)
                with lock:
                    database.save_full_state(parsed)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'{"success": true, "engine": "sqlite"}')
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
    print("=" * 60)
    print("  Initializing SQLite Database (store.db)...")
    database.init_db()
    stats = database.get_stats()
    print(f"  [OK] SQLite Ready! {stats['stock_items_count']} stock items | DB size: {stats['size_kb']} KB")
    print("=" * 60)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), KiranaHandler) as httpd:
        print(f"Room No 114 Kirana Server running on port {PORT}")
        print(f"Endpoints available:")
        print(f" - http://localhost:{PORT}/ (Web POS)")
        print(f" - http://localhost:{PORT}/api/sync (SQLite Sync Engine)")
        print(f" - http://localhost:{PORT}/api/db/stats (SQLite Database Metrics)")
        print(f" - http://localhost:{PORT}/api/db/backup (Download SQLite .db File)")
        httpd.serve_forever()
