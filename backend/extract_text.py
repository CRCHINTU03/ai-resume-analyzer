import os
import logging
import pdfplumber
from docx import Document

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_text(file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Extracting text from file: {file_path} with extension {ext}")

        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        elif ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                return text

        elif ext == '.docx':
            doc = Document(file_path)
            text = ''
            for para in doc.paragraphs:
                text += para.text + '\n'
            return text

        else:
            logger.error(f"Unsupported file extension: {ext}")
            raise ValueError(f"Unsupported file extension: {ext}")

    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}", exc_info=True)
        raise