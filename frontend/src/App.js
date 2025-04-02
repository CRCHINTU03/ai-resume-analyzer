// frontend/src/App.js
import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import Results from './components/Results';
import './App.css';

function App() {
    const [result, setResult] = useState(null);

    const handleResult = (data) => setResult(data);

    return (
        <div className="App">
            <h1>AI Resume Analyzer</h1>
            <div className="form-container">
                <UploadForm onResult={handleResult} />
            </div>
            {result && (
                <div className="results-container">
                    <Results result={result} />
                </div>
            )}
        </div>
    );
}

export default App;