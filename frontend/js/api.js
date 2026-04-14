export const parsePDF = async (formData) => {
    try {
        const response = await fetch('/parse', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to parse document');
        return data;
    } catch (error) { throw error; }
};

export const optimizeResume = async (payload) => {
    try {
        const response = await fetch('/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Optimization failed');
        return data;
    } catch (error) { throw error; }
};

export const analyzeMatch = async (resumeText, jobDesc) => {
    try {
        const response = await fetch('/match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume: resumeText, job_description: jobDesc })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to analyze match');
        return data;
    } catch (error) { throw error; }
};

export const generatePDF = async (payload) => {
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to generate PDF');
        return data;
    } catch (error) { throw error; }
};