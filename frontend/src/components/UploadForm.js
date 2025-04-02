import React, { useState } from 'react';
import axios from 'axios';

const UploadForm = ({ onResult }) => {
    const [resume, setResume] = useState(null);
    const [jobDescriptionFile, setJobDescriptionFile] = useState(null);
    const [jobDescriptionText, setJobDescriptionText] = useState('');
    const [jobDescriptionInputType, setJobDescriptionInputType] = useState('file'); // 'file' or 'text'
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

        setLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('resume', resume);
        if (jobDescriptionInputType === 'file') {
            formData.append('jobDescription', jobDescriptionFile);
        } else {
            formData.append('jobDescriptionText', jobDescriptionText);
        }

        try {
            const response = await axios.post('http://localhost:5001/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            onResult(response.data);
        } catch (err) {
            setError('An error occurred while processing your request.');
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
                ) : (
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