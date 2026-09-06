from flask import Flask, render_template, request, redirect, url_for, flash
import os
import subprocess
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads/'

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["achecker_db"]
collection = db["uploaded_files"]

@app.route('/')
def index():
    return render_template('index.html', output='')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save file details to MongoDB
        file_data = {
            'filename': filename,
            'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        collection.insert_one(file_data)

        output = run_achecker(file_path)
        return render_template('index.html', output=output)

def run_achecker(file_path):
    try:
        result = subprocess.run(
            ['python3', 'bin/achecker.py', '-f', file_path, '-b'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        cleaned_output = result.stdout.replace('\x1b[4m', '').replace('\x1b[0m', '')
        formatted_output = format_output(cleaned_output)
        return formatted_output
    except Exception as e:
        return str(e)

def format_output(output):
    sections = output.split('Checking contract for')
    formatted_sections = []

    for section in sections:
        if section.strip():
            header, *details = section.split('------------------')
            header = 'Checking contract for ' + header.strip()
            details = [line.strip() for line in details if line.strip()]
            formatted_section = f'<h3>{header}</h3><hr>'
            for detail in details:
                formatted_section += f'<pre>{detail}</pre>'
            formatted_sections.append(formatted_section)

    return '<div>' + ''.join(formatted_sections) + '</div>'

@app.route('/view-uploads')
def view_uploads():
    # Retrieve uploaded files from MongoDB
    files = list(collection.find().sort('upload_time', -1))
    return render_template('uploads.html', files=files)

if __name__ == '__main__':
    app.run(debug=True)
