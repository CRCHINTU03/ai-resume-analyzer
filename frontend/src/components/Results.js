import React from 'react';

const Results = ({ result }) => {
    if (!result) return null;

    return (
        <div className="card results">
            <h2>ATS Analysis Results</h2>
            <div className="ats-score">
                ATS Score: {result.ats_score}/100
            </div>
            <h3>Recommendations:</h3>
            {result.recommendations?.length > 0 ? (
                <ul className="recommendation-list">
                    {result.recommendations.map((rec, index) => (
                        <li key={index} className="recommendation-item">{rec}</li>
                    ))}
                </ul>
            ) : (
                <p>No recommendations available.</p>
            )}
            <h3>Missing Keywords:</h3>
            {result.missing_keywords?.length > 0 ? (
                <ul className="recommendation-list">
                    {result.missing_keywords.map((keyword, index) => (
                        <li key={index} className="recommendation-item">{keyword}</li>
                    ))}
                </ul>
            ) : (
                <p>No missing keywords.</p>
            )}
            <h3>Missing Skills:</h3>
            {result.missing_skills?.length > 0 ? (
                <ul className="recommendation-list">
                    {result.missing_skills.map((skill, index) => (
                        <li key={index} className="recommendation-item">{skill}</li>
                    ))}
                </ul>
            ) : (
                <p>No missing skills.</p>
            )}
            <h3>Missing Entities:</h3>
            {result.missing_entities?.length > 0 ? (
                <ul className="recommendation-list">
                    {result.missing_entities.map((entity, index) => (
                        <li key={index} className="recommendation-item">{entity}</li>
                    ))}
                </ul>
            ) : (
                <p>No missing entities.</p>
            )}
        </div>
    );
};

export default Results;