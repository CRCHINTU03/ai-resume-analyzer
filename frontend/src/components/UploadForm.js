import React, { useState } from 'react';
import axios from 'axios';

const UploadForm = ({ onResult }) => {
    const [resume, setResume] = useState(null);
    const [jobDescriptionFile, setJobDescriptionFile] = useState(null);
    const [jobDescriptionText, setJobDescriptionText] = useState('');
    const [jobUrl, setJobUrl] = useState(''); // New state for job URL
    const [jobDescriptionInputType, setJobDescriptionInputType] = useState('file'); // 'file', 'text', or 'url'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!resume) {
            setError('Please upload a resume file.');
            return;
        }
        if (jobDescriptionInputType === 'file' && !jobDescriptionFile) {
            setError('Please upload a job description file.');
            return;
        }
        if (jobDescriptionInputType === 'text' && !jobDescriptionText.trim()) {
            setError('Please enter the job description text.');
            return;
        }
        if (jobDescriptionInputType === 'url' && !jobUrl.trim()) {
            setError('Please enter a job URL.');
            return;
        }

        setLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('resume', resume);
        if (jobDescriptionInputType === 'file') {
            formData.append('jobDescription', jobDescriptionFile);
        } else if (jobDescriptionInputType === 'text') {
            formData.append('jobDescriptionText', jobDescriptionText);
        } else if (jobDescriptionInputType === 'url') {
            formData.append('jobUrl', jobUrl);
        }

        try {
            const response = await axios.post('http://localhost:5001/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            onResult(response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'An error occurred while processing your request.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card upload-form">
            <h2>Upload Your Files</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Resume:</label>
                    <input
                        type="file"
                        accept=".txt,.pdf,.docx"
                        onChange={(e) => setResume(e.target.files[0])}
                        className="form-input"
                    />
                </div>
                <div className="form-group">
                    <label>Job Description Input Type:</label>
                    <div className="input-type-toggle">
                        <label>
                            <input
                                type="radio"
                                value="file"
                                checked={jobDescriptionInputType === 'file'}
                                onChange={() => setJobDescriptionInputType('file')}
                            />
                            Upload File
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="text"
                                checked={jobDescriptionInputType === 'text'}
                                onChange={() => setJobDescriptionInputType('text')}
                            />
                            Paste Text
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="url"
                                checked={jobDescriptionInputType === 'url'}
                                onChange={() => setJobDescriptionInputType('url')}
                            />
                            Job URL
                        </label>
                    </div>
                </div>
                {jobDescriptionInputType === 'file' ? (
                    <div className="form-group">
                        <label>Job Description (File):</label>
                        <input
                            type="file"
                            accept=".txt,.pdf,.docx"
                            onChange={(e) => setJobDescriptionFile(e.target.files[0])}
                            className="form-input"
                        />
                    </div>
                ) : jobDescriptionInputType === 'text' ? (
                    <div className="form-group">
                        <label>Job Description (Text):</label>
                        <textarea
                            value={jobDescriptionText}
                            onChange={(e) => setJobDescriptionText(e.target.value)}
                            className="form-textarea"
                            placeholder="Paste the job description here..."
                            rows="5"
                        />
                    </div>
                ) : (
                    <div className="form-group">
                        <label>Job URL:</label>
                        <input
                            type="text"
                            value={jobUrl}
                            onChange={(e) => setJobUrl(e.target.value)}
                            className="form-input"
                            placeholder="Enter job posting URL (e.g., LinkedIn, Indeed)"
                        />
                    </div>
                )}
                <button type="submit" disabled={loading} className="analyze-button">
                    {loading ? (
                        <>
                            Processing
                            <span className="loading-spinner"></span>
                        </>
                    ) : (
                        'Analyze'
                    )}
                </button>
            </form>
            {error && <p className="error">{error}</p>}
        </div>
    );
};

export default UploadForm;