from http.server import BaseHTTPRequestHandler, HTTPServer
import json, subprocess

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path != '/api/v1/ops':
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
            action = data.get('action')
            payload = data.get('payload', {})

            if action == 'create_ec2':
                cmd = f"aws ec2 run-instances --image-id {payload.get('image_id')} --instance-type {payload.get('instance_type')} --region {payload.get('region')} --query 'Instances[0].InstanceId' --output text"

            elif action == 'terminate_ec2':
                cmd = f"aws ec2 terminate-instances --instance-ids {payload.get('instance_id')} --region {payload.get('region')}"

            elif action == 'describe_ec2':
                cmd = f"aws ec2 describe-instances --instance-ids {payload.get('instance_id')} --region {payload.get('region')} --query 'Reservations[0].Instances[0].State.Name' --output text"

            else:
                raise Exception('Invalid action')

            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=300)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(output)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

HTTPServer(('0.0.0.0', 9100), Handler).serve_forever()
