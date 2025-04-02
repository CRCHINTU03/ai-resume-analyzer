import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = []
    
    # Extract single-word keywords (nouns, verbs, adjectives)
    for token in doc:
        if not token.is_stop and not token.is_punct and token.pos_ in ["NOUN", "VERB", "ADJ"]:
            keywords.append(token.lemma_)  # Use lemma to match related terms (e.g., "coding" and "code")
    
    # Extract multi-word phrases (noun chunks)
    for chunk in doc.noun_chunks:
        if not all(token.is_stop or token.is_punct for token in chunk):
            keywords.append(chunk.text.lower())
    
    return list(set(keywords))

def extract_skills(text):
    # List of common skills/tools (expand this list as needed)
    common_skills = [
        "python", "java", "javascript", "sql", "machine learning", "data analysis",
        "aws", "azure", "docker", "kubernetes", "tensorflow", "pytorch",
        "excel", "tableau", "power bi", "git", "agile", "scrum"
    ]
    doc = nlp(text.lower())
    skills = []
    
    # Check for skills in noun chunks
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        for skill in common_skills:
            if skill in chunk_text:
                skills.append(skill)
    
    # Check for skills in single tokens
    for token in doc:
        if token.text.lower() in common_skills:
            skills.append(token.text.lower())
    
    return list(set(skills))

def extract_entities(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "NORP", "GPE", "DATE"]:
            entities.append(ent.text.lower())
    return list(set(entities))

def extract_experience(text):
    # Simple regex to find years of experience (e.g., "5 years", "3+ years")
    pattern = r'(\d+\+?)\s*(years?|yrs?)\s*(of)?\s*experience'
    matches = re.findall(pattern, text.lower())
    total_years = 0
    for match in matches:
        years = match[0].replace('+', '')
        try:
            total_years = max(total_years, int(years))
        except ValueError:
            continue
    return total_years

def compute_ats_score(resume_text, job_text):
    # Extract keywords, skills, and entities
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_text)
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)
    resume_entities = extract_entities(resume_text)
    job_entities = extract_entities(job_text)

    # Compute TF-IDF scores for keywords to prioritize important ones
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([job_text])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()[0]
    keyword_importance = dict(zip(feature_names, tfidf_scores))

    # Identify missing keywords and skills, sorted by importance
    missing_keywords = []
    for kw in job_keywords:
        if kw not in resume_keywords:
            # Check if the keyword (or a part of it) is in the TF-IDF features
            kw_score = max(keyword_importance.get(word, 0) for word in kw.split())
            missing_keywords.append((kw, kw_score))
    missing_keywords = [kw for kw, _ in sorted(missing_keywords, key=lambda x: x[1], reverse=True)][:10]  # Top 10 by importance

    missing_skills = [skill for skill in job_skills if skill not in resume_skills]
    missing_entities = [ent for ent in job_entities if ent not in resume_entities]

    # Compute keyword score using TF-IDF cosine similarity
    tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
    keyword_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100

    # Compute experience score (basic implementation)
    resume_years = extract_experience(resume_text)
    job_years = extract_experience(job_text)
    if job_years > 0:
        experience_score = min(resume_years / job_years, 1.0) * 100  # Normalize to 0-100
    else:
        experience_score = 100 if resume_years > 0 else 0  # If job doesn't specify years, assume experience is a bonus

    # Placeholder for BERT score
    bert_score = 0

    # Weighted ATS score
    ats_score = (keyword_score * 0.5) + (experience_score * 0.4) + (bert_score * 0.1)

    # Generate detailed recommendations
    recommendations = []
    if missing_keywords:
        recommendations.append("Add the following keywords to your resume, preferably in the skills, experience, or summary sections:")
        for kw in missing_keywords:
            recommendations.append(f"- {kw}")
    if missing_skills:
        recommendations.append("Consider adding these skills to your resume under a 'Skills' section:")
        for skill in missing_skills:
            recommendations.append(f"- {skill}")
    if missing_entities:
        recommendations.append("Incorporate these entities (e.g., organizations, dates) into your experience or education sections:")
        for ent in missing_entities:
            recommendations.append(f"- {ent}")
    if not missing_keywords and not missing_skills and not missing_entities:
        recommendations.append("Your resume aligns well with the job description. Consider tailoring it further by emphasizing quantifiable achievements.")

    return {
        "ats_score": round(ats_score, 2),
        "missing_keywords": missing_keywords,
        "missing_skills": missing_skills,
        "missing_entities": missing_entities,
        "recommendations": recommendations
    }