from flask import Flask, render_template_string
import json, os

app = Flask(__name__)

@app.route('/')
def home():
    manifest_path = './data/metadata/manifest.json'
    if not os.path.exists(manifest_path):
        return "<h2>No manifest file found yet</h2>"

    manifest = json.load(open(manifest_path))
    html = """
    <html>
    <head><title>BU Research Data Lake Dashboard</title></head>
    <body>
    <h2>Recent ETL Files</h2>
    <table border="1" cellpadding="5">
    <tr><th>Filename</th><th>Hash</th><th>Timestamp</th></tr>
    {% for m in manifest[-10:] %}
    <tr><td>{{ m.filename }}</td><td>{{ m.hash }}</td><td>{{ m.timestamp }}</td></tr>
    {% endfor %}
    </table>
    </body></html>
    """
    return render_template_string(html, manifest=manifest)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
