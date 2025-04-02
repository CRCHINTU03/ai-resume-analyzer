import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from extract_text import extract_text
from ats_score01 import compute_ats_score

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.route('/')
def serve():
    logger.info("Serving index.html")
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    logger.info(f"Serving static file: {path}")
    return send_from_directory(app.static_folder, path)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'resume' not in request.files:
            logger.error("Missing resume file in request")
            return jsonify({'error': 'Resume file is required'}), 400

        resume_file = request.files['resume']
        job_description_text = request.form.get('jobDescriptionText', '').strip()

        if resume_file.filename == '':
            logger.error("Empty resume file submitted")
            return jsonify({'error': 'Empty resume file submitted'}), 400

        if not job_description_text and 'jobDescription' not in request.files:
            logger.error("Missing job description (file or text)")
            return jsonify({'error': 'Job description (file or text) is required'}), 400

        os.makedirs('uploads', exist_ok=True)
        resume_path = os.path.join('uploads', resume_file.filename)
        logger.info(f"Saving resume file: {resume_path}")
        resume_file.save(resume_path)

        resume_text = extract_text(resume_path)
        logger.info("Extracted text from resume")

        if job_description_text:
            # Job description provided as text
            job_text = job_description_text
            logger.info("Using job description text directly")
        else:
            # Job description provided as a file
            job_desc_file = request.files['jobDescription']
            if job_desc_file.filename == '':
                logger.error("Empty job description file submitted")
                return jsonify({'error': 'Empty job description file submitted'}), 400

            job_desc_path = os.path.join('uploads', job_desc_file.filename)
            logger.info(f"Saving job description file: {job_desc_path}")
            job_desc_file.save(job_desc_path)
            job_text = extract_text(job_desc_path)
            logger.info("Extracted text from job description file")
            os.remove(job_desc_path)

        logger.info("Computing ATS score")
        ats_result = compute_ats_score(resume_text, job_text)

        logger.info("Cleaning up temporary files")
        os.remove(resume_path)

        return jsonify(ats_result), 200

    except Exception as e:
        logger.error(f"Error in /upload: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)