const API_URL = 'http://localhost:5000';

export const analyzeMatch = async (resumeText, jobDesc) => {
    try {
        const response = await fetch(`${API_URL}/match`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume: resumeText, job_description: jobDesc })
        });
        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        return null;
    }
};

export const generatePDF = async (payload) => {
    try {
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        return null;
    }
};
