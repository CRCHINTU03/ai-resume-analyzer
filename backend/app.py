import os
import logging
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from werkzeug.utils import secure_filename
from extract_text import extract_text
from ats_score01 import compute_ats_score
import spacy
import torch
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend/build/static', template_folder='../frontend/build')
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload size

# Directory for temporary files and model cache
UPLOAD_FOLDER = 'uploads'
CACHE_DIR = '/tmp/models'  # Use /tmp for Heroku ephemeral storage
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Lazy-loaded models (initialized on first use)
class ModelLoader:
    _nlp = None
    _transformer_model = None
    _transformer_tokenizer = None
    _sentence_model = None

    @staticmethod
    def get_nlp():
        if ModelLoader._nlp is None:
            try:
                logger.info("Downloading spaCy model 'en_core_web_sm'")
                spacy.cli.download("en_core_web_sm")
                ModelLoader._nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {str(e)}")
                raise
        return ModelLoader._nlp

    @staticmethod
    def get_transformer():
        if ModelLoader._transformer_model is None or ModelLoader._transformer_tokenizer is None:
            try:
                logger.info("Downloading transformer model 'bert-base-uncased'")
                ModelLoader._transformer_model = AutoModel.from_pretrained("bert-base-uncased", cache_dir=CACHE_DIR)
                ModelLoader._transformer_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased", cache_dir=CACHE_DIR)
            except Exception as e:
                logger.error(f"Failed to load transformer model: {str(e)}")
                raise
        return ModelLoader._transformer_model, ModelLoader._transformer_tokenizer

    @staticmethod
    def get_sentence_transformer():
        if ModelLoader._sentence_model is None:
            try:
                logger.info("Downloading sentence-transformer model 'all-MiniLM-L6-v2'")
                ModelLoader._sentence_model = SentenceTransformer("all-MiniLM-L6-v2", cache_dir=CACHE_DIR)
            except Exception as e:
                logger.error(f"Failed to load sentence-transformer model: {str(e)}")
                raise
        return ModelLoader._sentence_model

@app.route('/')
def serve():
    logger.info("Serving index.html")
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    logger.info(f"Serving static file: {path}")
    return send_from_directory(app.static_folder, path)

def scrape_job(url):
    """Scrape job description from a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        job_text = soup.find('div', class_='job-description') or soup.find('section', class_='description')
        return job_text.get_text(strip=True) if job_text else "Unable to scrape job description."
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {str(e)}")
        return f"Error scraping URL: {str(e)}"

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Check for resume file
        if 'resume' not in request.files:
            logger.error("Missing resume file in request")
            return jsonify({'error': 'Resume file is required'}), 400

        resume_file = request.files['resume']
        job_description_text = request.form.get('jobDescriptionText', '').strip()
        job_url = request.form.get('jobUrl', '').strip()

        if resume_file.filename == '' or not resume_file:
            logger.error("Empty or invalid resume file submitted")
            return jsonify({'error': 'Empty or invalid resume file submitted'}), 400

        # Validate job description input
        if not job_description_text and 'jobDescription' not in request.files and not job_url:
            logger.error("Missing job description (file, text, or URL)")
            return jsonify({'error': 'Job description (file, text, or URL) is required'}), 400

        # Save and process resume
        resume_path = os.path.join(UPLOAD_FOLDER, secure_filename(resume_file.filename))
        logger.info(f"Saving resume file: {resume_path}")
        resume_file.save(resume_path)
        resume_text = extract_text(resume_path)
        if not resume_text.strip():
            logger.error("No text extracted from resume")
            os.remove(resume_path)
            return jsonify({'error': 'Unable to extract text from resume'}), 400

        # Process job description
        if job_url:
            logger.info(f"Scraping job description from URL: {job_url}")
            job_text = scrape_job(job_url)
            if "Error" in job_text:
                os.remove(resume_path)
                return jsonify({'error': job_text}), 400
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

        # Load models and compute ATS score
        logger.info("Loading models and computing ATS score")
        nlp = ModelLoader.get_nlp()
        transformer_model, transformer_tokenizer = ModelLoader.get_transformer()
        sentence_model = ModelLoader.get_sentence_transformer()

        # Pass models to compute_ats_score (assumes it accepts these as kwargs)
        ats_result = compute_ats_score(
            resume_text,
            job_text,
            nlp=nlp,
            transformer_model=transformer_model,
            transformer_tokenizer=transformer_tokenizer,
            sentence_model=sentence_model
        )

        # Clean up
        logger.info("Cleaning up temporary files")
        os.remove(resume_path)

        return jsonify(ats_result), 200

    except Exception as e:
        logger.error(f"Error in /upload: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/download_report', methods=['POST'])
def download_report():
    try:
        ats_result = request.json
        if not ats_result:
            logger.error("No ATS result provided for download")
            return jsonify({'error': 'No analysis result provided'}), 400

        # Generate PDF
        pdf_path = os.path.join(UPLOAD_FOLDER, 'ats_report.pdf')
        pdf = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = [
            Paragraph(f"ATS Score: {ats_result['ats_score']}%"),
            Paragraph(f"Skills Score: {ats_result['skills_score']}%"),
            Paragraph(f"Experience Score: {ats_result['experience_score']}%"),
            Paragraph("Recommendations:")
        ]
        for rec in ats_result['recommendations']:
            story.append(Paragraph(rec))
        pdf.build(story)

        logger.info("Generated PDF report")
        return send_file(pdf_path, as_attachment=True, download_name='ats_report.pdf')

    except Exception as e:
        logger.error(f"Error in /download_report: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to generate report'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))