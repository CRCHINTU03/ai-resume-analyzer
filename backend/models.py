# backend/models.py
import logging
from sentence_transformers import SentenceTransformer
import spacy

logger = logging.getLogger(__name__)

# Global variables for lazy loading
nlp = None
sentence_model = None
CACHE_DIR = '/tmp/models'

def load_nlp():
    global nlp
    if nlp is None:
        try:
            logger.info("Downloading spaCy model 'en_core_web_sm'")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {str(e)}")
            raise
    return nlp

def load_sentence_transformer():
    global sentence_model
    if sentence_model is None:
        try:
            logger.info("Downloading sentence-transformer model 'all-MiniLM-L6-v2'")
            sentence_model = SentenceTransformer("all-MiniLM-L6-v2", cache_dir=CACHE_DIR)
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer model: {str(e)}")
            raise
    return sentence_model