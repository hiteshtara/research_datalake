from flask import Flask, render_template_string, send_file
import pandas as pd, json, os, datetime, io

app = Flask(__name__)

# -------- CONFIG --------
MANIFEST_PATH = './data/metadata/manifest.json'
RUNTIME_CSV = './logs/etl_runtime_stats.csv'

# -------- ROUTES --------
@app.route('/')
def dashboard():
    manifest_data = []
    runtime_df = None

    # Load manifest
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r') as f:
            try:
                manifest_data = json.load(f)
            except json.JSONDecodeError:
                manifest_data = []
    manifest_data = manifest_data[-10:] if manifest_data else []

    # Load runtime data
    if os.path.exists(RUNTIME_CSV):
        runtime_df = pd.read_csv(RUNTIME_CSV)
        runtime_df = runtime_df.tail(10)  # last 10 runs

    html = """
    <!doctype html>
    <html>
    <head>
        <title>BU Research Data Lake Dashboard</title>
        <meta http-equiv="refresh" content="120">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial; margin: 40px; }
            table { border-collapse: collapse; width: 80%; margin-bottom: 40px; }
            th, td { padding: 8px 12px; border: 1px solid #ccc; text-align: left; }
            th { background-color: #f5f5f5; }
            .success { color: green; font-weight: bold; }
            .failure { color: red; font-weight: bold; }
            .download-btn {
                background-color: #007bff;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                border-radius: 5px;
                cursor: pointer;
            }
            .download-btn:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <h1>📊 BU Research Data Lake Dashboard</h1>
        <h3>Recent ETL Manifest Entries</h3>
        <table>
            <tr><th>Filename</th><th>Hash</th><th>Timestamp</th></tr>
            {% for m in manifest_data %}
            <tr>
                <td>{{ m.filename }}</td>
                <td>{{ m.hash }}</td>
                <td>{{ m.timestamp }}</td>
            </tr>
            {% endfor %}
        </table>

        {% if runtime_df is not none %}
        <h3>Recent Runtime Trends (last 10 runs)</h3>
        <canvas id="runtimeChart" width="800" height="300"></canvas>
        <script>
        const ctx = document.getElementById('runtimeChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ runtime_df.date.tolist()|safe }},
                datasets: [{
                    label: 'Runtime (minutes)',
                    data: {{ runtime_df.runtime_min.tolist()|safe }},
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Minutes' }
                    }
                }
            }
        });
        </script>

        <h3>Run History (Last 10 Days)</h3>
        <table>
            <tr><th>Date</th><th>Runtime (min)</th><th>Status</th></tr>
            {% for i, row in runtime_df.iterrows() %}
            <tr>
                <td>{{ row.date }}</td>
                <td>{{ "%.2f"|format(row.runtime_min) }}</td>
                <td class="{{ row.status }}">{{ row.status }}</td>
            </tr>
            {% endfor %}
        </table>

        <form action="/download" method="get">
            <button type="submit" class="download-btn">⬇️ Download Full CSV</button>
        </form>
        {% else %}
        <p>No runtime data found yet. Run the ETL at least once.</p>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(html, manifest_data=manifest_data, runtime_df=runtime_df)


@app.route('/download')
def download_csv():
    """Serve the entire ETL runtime CSV for download."""
    if not os.path.exists(RUNTIME_CSV):
        return "No CSV file found yet.", 404

    # Stream the CSV to avoid filesystem permissions issues
    with open(RUNTIME_CSV, 'rb') as f:
        data = io.BytesIO(f.read())
    data.seek(0)
    filename = f"etl_runtime_stats_{datetime.date.today()}.csv"
    return send_file(data, mimetype='text/csv', as_attachment=True, download_name=filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
