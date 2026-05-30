import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Serve the file if it exists, otherwise fallback to index.html
        path = self.translate_path(self.path)
        if not os.path.exists(path) or not os.path.isfile(path):
            # Try to serve index.html for SPA fallback
            if not self.path.startswith('/assets/'):
                self.path = '/index.html'
        return super().do_GET()

    def end_headers(self):
        # Prevent caching of index.html and SPA routing fallbacks
        if self.path.endswith('.html') or self.path == '/' or not '.' in self.path:
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving SPA at port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
