from http.server import BaseHTTPRequestHandler, HTTPServer
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
            request_id = data.get('requestId', None)
            action = data.get('action')
            payload = data.get('payload', {})

            if not action:
                raise Exception("Missing action")

            if action == 'create_ec2':
                cmd = f"aws ec2 run-instances --image-id {payload.get('image_id')} --instance-type {payload.get('instance_type')} --region {payload.get('region')} --query 'Instances[0].InstanceId' --output text"

            elif action == 'terminate_ec2':
                cmd = f"aws ec2 terminate-instances --instance-ids {payload.get('instance_id')} --region {payload.get('region')}"

            elif action == 'describe_ec2':
                cmd = f"aws ec2 describe-instances --instance-ids {payload.get('instance_id')} --region {payload.get('region')} --query 'Reservations[0].Instances[0].State.Name' --output text"

            elif action == 'sts_identity':
                cmd = "aws sts get-caller-identity"

            else:
                raise Exception("Invalid action")

            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=300)

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(f"action={action} requestId={request_id} success=true duration_ms={duration_ms}")

            response = {
                "requestId": request_id,
                "success": True,
                "data": output.decode().strip(),
                "error": None
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(f"action={action if 'action' in locals() else None} requestId={request_id if 'request_id' in locals() else None} success=false duration_ms={duration_ms}")

            response = {
                "requestId": request_id if 'request_id' in locals() else None,
                "success": False,
                "data": None,
                "error": str(e)
            }

            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())


HTTPServer(('0.0.0.0', 9100), Handler).serve_forever()
