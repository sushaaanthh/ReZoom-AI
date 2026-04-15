const API_BASE = 'https://rezoom-backend.onrender.com';

export const parsePDF = async (formData) => {
    const res = await fetch(`${API_BASE}/parse`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
};

export const optimizeResume = async (payload) => {
    const res = await fetch(`${API_BASE}/optimize`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
};

export const analyzeMatch = async (resumeJsonStr, jobDesc, filename) => {
    const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_data: resumeJsonStr, job_description: jobDesc, filename: filename })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
};

export const generatePDF = async (payload) => {
    const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    return { download_url: url };
};