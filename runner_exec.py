from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maas-core")


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path != '/api/v1/ops':
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        start_time = time.time()

        try:
            data = json.loads(body)
            request_id = data.get("requestId")
            action = data.get("action")
            payload = data.get("payload", {})

            if action == "sts_identity":
                result = subprocess.check_output(
                    ["aws", "sts", "get-caller-identity"],
                    stderr=subprocess.STDOUT
                ).decode()

                response = {
                    "requestId": request_id,
                    "success": True,
                    "data": result,
                    "error": None
                }

            elif action == "history":
                response = {
                    "requestId": request_id,
                    "success": True,
                    "data": [],
                    "error": None
                }

            else:
                response = {
                    "requestId": request_id,
                    "success": False,
                    "data": None,
                    "error": f"Unknown action: {action}"
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

            duration = round((time.time() - start_time) * 1000, 2)
            logger.info(f"{action} handled in {duration} ms")

        except Exception as e:
            logger.exception("Request failed")

            response = {
                "requestId": None,
                "success": False,
                "data": None,
                "error": str(e)
            }

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())


def run():
    server_address = ('0.0.0.0', 9100)
    httpd = ThreadingHTTPServer(server_address, Handler)
    logger.info("MaaS Core API starting on port 9100")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
