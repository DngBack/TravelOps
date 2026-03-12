"""
Vercel Python entrypoint so the build passes.
TravelOps is a Streamlit app — for full UI, deploy on Streamlit Community Cloud:
https://share.streamlit.io (connect this repo, set OPENAI_API_KEY).
"""
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        body = """
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><title>TravelOps</title></head>
        <body style="font-family:sans-serif;max-width:560px;margin:2rem auto;padding:1rem;">
          <h1>✈️ TravelOps</h1>
          <p>This repo is a <strong>Streamlit</strong> app. Vercel does not run Streamlit.</p>
          <p>To run the full UI:</p>
          <ul>
            <li><a href="https://share.streamlit.io">Streamlit Community Cloud</a> — connect this GitHub repo, add <code>OPENAI_API_KEY</code>, done.</li>
            <li>Or locally: <code>streamlit run app.py</code></li>
          </ul>
        </body></html>
        """
        self.wfile.write(body.encode("utf-8"))

    def do_POST(self):
        self.do_GET()
