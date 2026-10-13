import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest

from core.client import BenchmarkError, list_datasets
from core import client
from mcp.server import handle


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps([
            {"id": 2, "name": "GSM8K", "adapter_id": "numeric", "version": "test", "item_count": 3, "api_key": "sk-secret"},
        ]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


class ClientTests(unittest.TestCase):
    def test_list_datasets_drops_secrets(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        port = server.server_address[1]
        original = client.base_url
        client.base_url = lambda: f"http://127.0.0.1:{port}"
        self.addCleanup(lambda: setattr(client, "base_url", original))
        rows = list_datasets()
        self.assertEqual(rows, [{
            "id": 2,
            "name": "GSM8K",
            "adapter_id": "numeric",
            "version": "test",
            "item_count": 3,
        }])
        self.assertNotIn("sk-secret", json.dumps(rows))

    def test_tools_list(self):
        response = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertIn("benchmark_list_datasets", names)
        self.assertIn("benchmark_start_experiment", names)

    def test_missing_service(self):
        original = client.base_url
        client.base_url = lambda: "http://127.0.0.1:9"
        self.addCleanup(lambda: setattr(client, "base_url", original))
        with self.assertRaises(BenchmarkError):
            client.health()


if __name__ == "__main__":
    unittest.main()
