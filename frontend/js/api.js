async function handleResponse(response) {
    const contentType = response.headers.get("content-type");
    
    if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || `Server Error: ${response.status}`);
        }
        return data;
    }
    
    throw new Error(`Invalid response endpoint. Access the app directly via http://127.0.0.1:5000`);
}

export const parsePDF = async (formData) => {
    try {
        const response = await fetch('/parse', {
            method: 'POST',
            body: formData
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
};

export const optimizeResume = async (payload) => {
    try {
        const response = await fetch('/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
};

export const analyzeMatch = async (resumeText, jobDesc) => {
    try {
        const response = await fetch('/match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume: resumeText, job_description: jobDesc })
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
};

export const generatePDF = async (payload) => {
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
};