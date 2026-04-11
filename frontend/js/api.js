const API_URL = 'http://localhost:5000';

export const analyzeMatch = async (resumeText, jobDesc) => {
    try {
        const response = await fetch(`${API_URL}/match`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume: resumeText, job_description: jobDesc })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to analyze match');
        return data;
    } catch (error) {
        throw error;
    }
};

export const generatePDF = async (payload) => {
    try {
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to generate PDF');
        return data;
    } catch (error) {
        throw error;
    }
};