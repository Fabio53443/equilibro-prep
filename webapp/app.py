from flask import Flask, request, jsonify, send_file, send_from_directory
import csv
import os
from werkzeug.utils import secure_filename
from process_csv import process_csv
import sys
import uuid
import threading
import time

app = Flask(__name__)
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
SCHOOLS_FILE = os.path.join(os.path.dirname(__file__), 'static', 'scuolelazio.csv')
INPUT_FILE = os.path.join(os.path.dirname(__file__), 'static', 'input.csv')
 
# Add the parent directory to sys.path so process_csv can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load schools data into memory for filtering
with open(SCHOOLS_FILE, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    schools = list(reader)

@app.route('/api/schools', methods=['GET'])
def get_schools():
    # Filter by query params (additive/OR logic)
    filters = {k: v for k, v in request.args.items() if v}
    filtered = schools
    for key, value in filters.items():
        values = [v.strip().lower() for v in value.split('|') if v.strip()]
        if values:
            filtered = [s for s in filtered if s.get(key, '').lower() in values]
    return jsonify(filtered)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return jsonify({'filename': filename})

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    selected_schools = data.get('schools', [])
    # Generate a short unique ID for this session/request
    unique_id = uuid.uuid4().hex[:8]
    # Use the default input file in the root folder
    input_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'input.csv'))
    process_csv(input_path, set(selected_schools) if selected_schools else None)
    base_name = os.path.splitext(input_path)[0]
    output1 = f"{base_name}_output1.csv"
    output2 = f"{base_name}_output2.csv"
    # Unique output filenames
    out1_name = f'CercaListe_{unique_id}.csv'
    out2_name = f'listelibri_{unique_id}.csv'
    scuoleterritorio_name = f'scuoleterritorio_{unique_id}.csv'
    os.replace(output1, os.path.join(OUTPUT_FOLDER, out1_name))
    os.replace(output2, os.path.join(OUTPUT_FOLDER, out2_name))
    scuoleterritorio_path = os.path.join(OUTPUT_FOLDER, scuoleterritorio_name)
    with open(scuoleterritorio_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['NomeScuola', 'CodiceMeccanografico'])
        for s in schools:
            if not selected_schools or s['CODICESCUOLA'] in selected_schools:
                writer.writerow([s['DENOMINAZIONESCUOLA'], s['CODICESCUOLA']])
    return jsonify({'output1': out1_name, 'output2': out2_name, 'scuoleterritorio': scuoleterritorio_name, 'unique_id': unique_id})

def schedule_delete(filepath, delay=120):
    def delete_file():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
    threading.Thread(target=delete_file, daemon=True).start()

@app.route('/api/download/<filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    schedule_delete(file_path, delay=120)
    return send_file(file_path, as_attachment=True)

@app.route('/')
def root():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/webapp/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.dirname(__file__), filename)

if __name__ == '__main__':
    app.run(debug=True)
