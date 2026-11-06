#!/usr/bin/env python3
"""HTTP 示例服务端（仅标准库）。python server.py 后监听 127.0.0.1:8765/data.json"""
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({
            "type": "snapshot",
            "data": {"items": [{
                "event_id": "http-1", "name": "接口自定义事件",
                "lat": 35.68, "lon": 139.69, "mag": 3.8,
                "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }]},
            "metrics": [{"id": "rtt", "label": "接口延迟", "value": 12, "unit": "ms"}],
        }, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8765), H).serve_forever()
