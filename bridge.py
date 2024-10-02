import http.server
import socketserver
import json
import urllib.request
import urllib.parse

# Configuration
BRIDGE_PORT = 6000
LM_STUDIO_URL = "http://host.docker.internal:1234/v1/chat/completions"


class BridgeHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        cheshire_request = json.loads(post_data.decode("utf-8"))

        # Extract the text from Cheshire Cat's request
        full_text = cheshire_request.get("text", "")

        # Split the text into system message and user messages
        parts = full_text.split("Human: ")
        system_message = parts[0].strip()
        user_messages = [msg.strip() for msg in parts[1:] if msg.strip()]

        # Prepare messages for LM Studio
        messages = [{"role": "system", "content": system_message}]
        for msg in user_messages:
            messages.append({"role": "user", "content": msg})

        # Prepare the request for LM Studio
        lm_studio_data = json.dumps(
            {
                "model": "TheBloke/Llama-2-7B-Chat-GGUF",  # Adjust as needed
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150,
                "stream": False,
            }
        ).encode("utf-8")

        lm_studio_req = urllib.request.Request(
            LM_STUDIO_URL, data=lm_studio_data, method="POST"
        )
        lm_studio_req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(lm_studio_req) as lm_studio_response:
                lm_studio_result = json.loads(lm_studio_response.read().decode("utf-8"))
                generated_text = lm_studio_result["choices"][0]["message"]["content"]

                # Send the response back to Cheshire Cat
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = json.dumps({"text": generated_text})
                self.wfile.write(response.encode("utf-8"))
        except urllib.error.URLError as e:
            self.send_error(500, f"Error communicating with LM Studio: {str(e)}")


if __name__ == "__main__":
    with socketserver.TCPServer(("", BRIDGE_PORT), BridgeHandler) as httpd:
        print(f"Bridge server is running on port {BRIDGE_PORT}")
        httpd.serve_forever()
