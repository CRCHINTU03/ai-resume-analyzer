import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from sentence_transformers import SentenceTransformer, util
from collections import Counter

# Load models
nlp = spacy.load("en_core_web_sm")
bert_model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = []
    
    # Extract single-word keywords (nouns, verbs, adjectives)
    for token in doc:
        if not token.is_stop and not token.is_punct and token.pos_ in ["NOUN", "VERB", "ADJ"]:
            keywords.append(token.lemma_)
    
    # Extract multi-word phrases (noun chunks)
    for chunk in doc.noun_chunks:
        if not all(token.is_stop or token.is_punct for token in chunk):
            keywords.append(chunk.text.lower())
    
    # Add synonyms for key terms (e.g., "coding" -> "programming")
    synonyms = {
        "coding": ["programming", "development"],
        "data": ["analytics", "information"],
        "management": ["leadership", "oversight"]
    }
    expanded_keywords = []
    for kw in keywords:
        expanded_keywords.append(kw)
        for key, syn_list in synonyms.items():
            if key in kw:
                expanded_keywords.extend(syn_list)
    
    return list(set(expanded_keywords))

def extract_skills(text):
    # Expanded list of common skills/tools for iCIMS compatibility
    common_skills = [
        "python", "java", "javascript", "sql", "machine learning", "data analysis",
        "aws", "azure", "docker", "kubernetes", "tensorflow", "pytorch",
        "excel", "tableau", "power bi", "git", "agile", "scrum", "project management",
        "communication", "teamwork", "problem solving", "cloud computing", "devops"
    ]
    doc = nlp(text.lower())
    skills = []
    
    # Check for skills in text (including comma-separated lists)
    text_words = re.split(r'[,\s]+', text.lower())
    for skill in common_skills:
        if skill in text or skill in text_words:
            skills.append(skill)
    
    # Check noun chunks for multi-word skills
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        for skill in common_skills:
            if skill in chunk_text:
                skills.append(skill)
    
    return list(set(skills))

def extract_entities(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "NORP", "GPE", "DATE"]:
            entities.append(ent.text.lower())
    return list(set(entities))

def extract_experience(text):
    # Enhanced regex for experience (e.g., "5 years", "3+ years", "2018-2023")
    year_pattern = r'(\d+\+?)\s*(years?|yrs?)\s*(of)?\s*experience'
    range_pattern = r'(\d{4})\s*[-–]\s*(\d{4})'
    
    # Extract years from "X years" format
    year_matches = re.findall(year_pattern, text.lower())
    total_years = 0
    for match in year_matches:
        years = match[0].replace('+', '')
        try:
            total_years = max(total_years, int(years))
        except ValueError:
            continue
    
    # Extract years from date ranges (e.g., "2018-2023")
    range_matches = re.findall(range_pattern, text.lower())
    for start, end in range_matches:
        try:
            years = int(end) - int(start)
            total_years = max(total_years, years)
        except ValueError:
            continue
    
    return total_years

def compute_ats_score(resume_text, job_text):
    # Extract features
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_text)
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)
    resume_entities = extract_entities(resume_text)
    job_entities = extract_entities(job_text)

    # Compute BERT semantic similarity
    resume_embedding = bert_model.encode(resume_text, convert_to_tensor=True)
    job_embedding = bert_model.encode(job_text, convert_to_tensor=True)
    bert_score = util.cos_sim(resume_embedding, job_embedding).item() * 100

    # TF-IDF for keyword importance
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([job_text])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()[0]
    keyword_importance = dict(zip(feature_names, tfidf_scores))

    # Missing keywords and skills with importance
    missing_keywords = []
    for kw in job_keywords:
        if kw not in resume_keywords:
            kw_score = max(keyword_importance.get(word, 0) for word in kw.split())
            missing_keywords.append((kw, kw_score))
    missing_keywords = [kw for kw, _ in sorted(missing_keywords, key=lambda x: x[1], reverse=True)][:10]

    missing_skills = [skill for skill in job_skills if skill not in resume_skills]
    skills_score = (len([s for s in job_skills if s in resume_skills]) / max(len(job_skills), 1)) * 100

    missing_entities = [ent for ent in job_entities if ent not in resume_entities]

    # Keyword score via TF-IDF cosine similarity
    tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
    keyword_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100

    # Experience score with recency consideration
    resume_years = extract_experience(resume_text)
    job_years = extract_experience(job_text)
    if job_years > 0:
        experience_score = min(resume_years / job_years, 1.0) * 100
    else:
        experience_score = 100 if resume_years > 0 else 50  # Neutral if unspecified

    # Weighted ATS score (adjusted for iCIMS emphasis on skills and keywords)
    ats_score = (keyword_score * 0.35) + (bert_score * 0.25) + (skills_score * 0.25) + (experience_score * 0.15)

    # iCIMS-friendly recommendations
    recommendations = []
    if missing_keywords:
        recommendations.append("Incorporate these high-priority keywords into your resume (e.g., in skills, summary, or experience):")
        for kw in missing_keywords:
            recommendations.append(f"- {kw}")
    if missing_skills:
        recommendations.append("Add these skills in a dedicated 'Skills' section or within experience descriptions:")
        for skill in missing_skills:
            recommendations.append(f"- {skill}")
    if resume_years < job_years:
        recommendations.append(f"The job requires {job_years} years of experience, but your resume shows {resume_years}. Highlight more relevant experience if possible.")
    if not missing_keywords and not missing_skills:
        recommendations.append("Your resume aligns well with the job. Enhance it with specific achievements (e.g., 'Increased sales by 20%') for better impact.")

    return {
        "ats_score": round(ats_score, 2),
        "missing_keywords": missing_keywords,
        "missing_skills": missing_skills,
        "missing_entities": missing_entities,
        "skills_score": round(skills_score, 2),
        "experience_score": round(experience_score, 2),
        "recommendations": recommendations
    }

# Example usage (uncomment to test)
# resume = "Experienced Python developer with 5 years of experience in data analysis and AWS."
# job = "Seeking a Python developer with 7 years of experience in machine learning, AWS, and agile."
# result = compute_ats_score(resume, job)
# print(result)