# backend/app.py
import os
import logging
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from .extract_text import extract_text
from .ats_score01 import compute_ats_score
from .models import load_nlp, load_sentence_transformer

# Set up logging to stderr (Render will capture this in logs)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Log at startup to confirm imports and initialization
logger.info("Starting application...")
logger.info("Imports completed successfully")

# Log dependency versions at startup
def log_dependency_versions():
    import pkg_resources
    dependencies = ['torch', 'spacy', 'sentence_transformers', 'transformers']
    for dep in dependencies:
        try:
            version = pkg_resources.get_distribution(dep).version
            logger.info(f"Dependency {dep} version: {version}")
        except pkg_resources.DistributionNotFound:
            logger.warning(f"Dependency {dep} not installed")

log_dependency_versions()

app = Flask(__name__, static_folder='frontend/build/static', template_folder='frontend/build')
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload size

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Add a health check route for debugging
@app.route('/health')
def health():
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def serve():
    logger.info("Serving index.html")
    return send_from_directory(app.template_folder, 'index.html')

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
        job_url = request.form.get('jobUrl', '').strip()

        if resume_file.filename == '' or not resume_file:
            logger.error("Empty or invalid resume file submitted")
            return jsonify({'error': 'Empty or invalid resume file submitted'}), 400

        if not job_description_text and 'jobDescription' not in request.files and not job_url:
            logger.error("Missing job description (file, text, or URL)")
            return jsonify({'error': 'Job description (file, text, or URL) is required'}), 400

        resume_path = os.path.join(UPLOAD_FOLDER, secure_filename(resume_file.filename))
        logger.info(f"Saving resume file: {resume_path}")
        resume_file.save(resume_path)
        resume_text = extract_text(resume_path)
        if not resume_text.strip():
            logger.error("No text extracted from resume")
            os.remove(resume_path)
            return jsonify({'error': 'Unable to extract text from resume'}), 400

        if job_url:
            logger.error("URL scraping is disabled to reduce dependencies")
            os.remove(resume_path)
            return jsonify({'error': 'URL scraping is disabled'}), 400
        elif job_description_text:
            logger.info("Using job description text directly")
            job_text = job_description_text
        else:
            job_desc_file = request.files['jobDescription']
            if job_desc_file.filename == '' or not job_desc_file:
                logger.error("Empty or invalid job description file submitted")
                os.remove(resume_path)
                return jsonify({'error': 'Empty or invalid job description file submitted'}), 400
            job_desc_path = os.path.join(UPLOAD_FOLDER, secure_filename(job_desc_file.filename))
            logger.info(f"Saving job description file: {job_desc_path}")
            job_desc_file.save(job_desc_path)
            job_text = extract_text(job_desc_path)
            os.remove(job_desc_path)

        if not job_text.strip():
            logger.error("No text extracted from job description")
            os.remove(resume_path)
            return jsonify({'error': 'Unable to extract text from job description'}), 400

        logger.info("Loading models and computing ATS score")
        nlp_model = load_nlp()
        sentence_model_instance = load_sentence_transformer()

        ats_result = compute_ats_score(
            resume_text,
            job_text,
            nlp=nlp_model,
            sentence_model=sentence_model_instance
        )

        logger.info("Cleaning up temporary files")
        os.remove(resume_path)

        logger.info(f"ATS result: {ats_result}")
        return jsonify(ats_result), 200

    except Exception as e:
        logger.error(f"Error in /upload: {str(e)}", exc_info=True)
        if 'resume_path' in locals() and os.path.exists(resume_path):
            os.remove(resume_path)
        if 'job_desc_path' in locals() and os.path.exists(job_desc_path):
            os.remove(job_desc_path)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))

logger.info("Application startup completed")