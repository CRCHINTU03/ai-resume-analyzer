import spacy
import os
from pathlib import Path

# Load the English model
nlp = spacy.load("en_core_web_sm")

def preprocess_text(text):
    """
    Preprocess text using spaCy: tokenize, remove stop words, lemmatize, and normalize.
    Args:
        text (str): Raw text to preprocess.
    Returns:
        str: Preprocessed text as a single string.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.is_alpha]
    return " ".join(tokens)

def read_and_preprocess_file(file_path):
    """
    Read a text file and preprocess its contents.
    Args:
        file_path (str): Path to the text file.
    Returns:
        str: Preprocessed text.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return preprocess_text(text)
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return ""

def save_preprocessed_text(text, output_path):
    """
    Save preprocessed text to a file.
    Args:
        text (str): Preprocessed text to save.
        output_path (str): Path to save the text file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"Successfully saved preprocessed text to: {output_path}")
    except Exception as e:
        print(f"Error saving preprocessed text to {output_path}: {str(e)}")

def preprocess_folder(input_folder, output_folder):
    """
    Preprocess all text files in a folder and save the results.
    Args:
        input_folder (str): Path to the input folder.
        output_folder (str): Path to the output folder.
    """
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Get all .txt files in the input folder
    text_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".txt")]
    print(f"Found {len(text_files)} text files in {input_folder}: {text_files}")

    # Process each text file
    for text_file in text_files:
        input_path = os.path.join(input_folder, text_file)
        output_path = os.path.join(output_folder, text_file)
        
        print(f"\nProcessing: {text_file}")
        preprocessed_text = read_and_preprocess_file(input_path)
        
        # Save the preprocessed text
        save_preprocessed_text(preprocessed_text, output_path)
        
        # Print first 200 characters to verify
        print(f"Preprocessed text (first 200 characters): {preprocessed_text[:200]}")

if __name__ == "__main__":
    # Preprocess resumes
    preprocess_folder("data/extracted_resumes", "data/preprocessed_resumes")
    
    # Preprocess job descriptions
    preprocess_folder("data/job_descriptions", "data/preprocessed_jobs")