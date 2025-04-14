# backend/models.py
import logging
from sentence_transformers import SentenceTransformer
import spacy

logger = logging.getLogger(__name__)

nlp = None
sentence_model = None
CACHE_DIR = '/tmp/models'

def load_nlp():
    global nlp
    if nlp is None:
        try:
            logger.info("Loading spaCy model 'en_core_web_sm'")
            nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {str(e)}")
            raise
    return nlp

def load_sentence_transformer():
    global sentence_model
    if sentence_model is None:
        try:
            logger.info("Loading sentence-transformer model 'all-MiniLM-L6-v2'")
            sentence_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=CACHE_DIR)
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer model: {str(e)}")
            raise
    return sentence_model