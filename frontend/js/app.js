import { analyzeMatch, generatePDF } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeNavigation();
    initializeTemplateSelection();
    bindMakerEvents();
    bindOptimizerEvents();
    bindAnalyzerEvents();
});

function showNotification(message, type = 'info') {
    let container = document.getElementById('notification-area');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-area';
        container.className = 'notification-area';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;
    
    container.appendChild(toast);
    
    void toast.offsetWidth; 
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    if (!themeToggle) return;

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        document.body.classList.toggle('dark-mode');
        themeIcon.setAttribute('data-lucide', document.body.classList.contains('light-mode') ? 'moon' : 'sun');
        lucide.createIcons();
    });
}

function initializeNavigation() {
    const navIcons = document.querySelectorAll('.nav-icon');
    const tabContents = document.querySelectorAll('.tab-content');
    const analyticsPanel = document.getElementById('analytics-panel');
    
    if (analyticsPanel) analyticsPanel.classList.add('hidden');

    navIcons.forEach(icon => {
        icon.addEventListener('click', () => {
            if (!icon.hasAttribute('data-target')) return;

            navIcons.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            icon.classList.add('active');
            const targetId = icon.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            if (analyticsPanel) {
                if (targetId === 'tab-score') {
                    analyticsPanel.classList.remove('hidden');
                } else {
                    analyticsPanel.classList.add('hidden');
                }
            }
        });
    });
}

function initializeTemplateSelection() {
    window.selectedTemplate = 'base';
    const tempCards = document.querySelectorAll('.template-card');
    tempCards.forEach(card => {
        card.addEventListener('click', () => {
            tempCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            window.selectedTemplate = card.getAttribute('data-template');
        });
    });
}

function bindMakerEvents() {
    const makerUpload = document.getElementById('maker-upload');
    const btnExportMaker = document.getElementById('btn-export-maker');

    if (makerUpload) {
        makerUpload.addEventListener('change', async (e) => {
            if (!e.target.files[0]) return;
            
            const formData = new FormData();
            formData.append('file', e.target.files[0]);
            
            const uploadBox = e.target.parentElement;
            const originalHTML = uploadBox.innerHTML;
            uploadBox.innerHTML = '<i data-lucide="loader" class="spin"></i><p>Parsing PDF...</p>';
            lucide.createIcons();

            try {
                const response = await fetch('http://localhost:5000/parse', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || "Failed to parse document");
                
                document.getElementById('maker-exp').value = data.extracted_text || "";
                showNotification("PDF parsed successfully", "success");
            } catch (error) {
                showNotification(error.message, "error");
            } finally {
                uploadBox.innerHTML = originalHTML;
                lucide.createIcons();
            }
        });
    }

    if (btnExportMaker) {
        btnExportMaker.addEventListener('click', async () => {
            const payload = {
                name: document.getElementById('maker-name').value || "Applicant Name",
                email: document.getElementById('maker-email').value || "email@example.com",
                education: document.getElementById('maker-edu').value || "",
                experience: document.getElementById('maker-exp').value || "",
                skills: document.getElementById('maker-skills').value || "",
                template: window.selectedTemplate || 'base'
            };

            const originalText = btnExportMaker.innerHTML;
            btnExportMaker.innerHTML = '<i data-lucide="loader" class="spin"></i> Generating...';
            btnExportMaker.disabled = true;
            lucide.createIcons();

            try {
                const response = await generatePDF(payload);
                if (response && response.download_url) {
                    window.open(`http://localhost:5000${response.download_url}`, '_blank');
                    showNotification("Resume generated successfully", "success");
                }
            } catch (error) {
                showNotification(error.message, "error");
            } finally {
                btnExportMaker.innerHTML = originalText;
                btnExportMaker.disabled = false;
                lucide.createIcons();
            }
        });
    }
}

function bindOptimizerEvents() {
    const btnOptimize = document.getElementById('btn-optimize');
    if (!btnOptimize) return;

    btnOptimize.addEventListener('click', async () => {
        const fileInput = document.getElementById('match-upload').files[0];
        const jobDesc = document.getElementById('match-job-desc').value;

        if (!fileInput || !jobDesc.trim()) {
            showNotification("Please provide both a PDF and a Job Description.", "error");
            return;
        }

        const originalText = btnOptimize.innerHTML;
        btnOptimize.innerHTML = '<i data-lucide="loader" class="spin"></i> Optimizing...';
        btnOptimize.disabled = true;
        lucide.createIcons();

        try {
            const formData = new FormData();
            formData.append('file', fileInput);
            const parseRes = await fetch('http://localhost:5000/parse', { method: 'POST', body: formData });
            const parseData = await parseRes.json();
            if (!parseRes.ok) throw new Error(parseData.error || "Parsing failed");

            const payload = {
                name: "Tailored Applicant",
                email: "tailored@example.com",
                education: "Extracted Education",
                experience: `[Optimized Content]\n\n${parseData.extracted_text.substring(0, 800)}`,
                skills: "Optimized Skills",
                template: "modern"
            };

            const response = await generatePDF(payload);
            if (response && response.download_url) {
                document.getElementById('match-results').classList.remove('hidden');
                document.getElementById('btn-export-match').onclick = () => {
                    window.open(`http://localhost:5000${response.download_url}`, '_blank');
                };
                showNotification("Optimization complete", "success");
            }
        } catch (error) {
            showNotification(error.message, "error");
        } finally {
            btnOptimize.innerHTML = originalText;
            btnOptimize.disabled = false;
            lucide.createIcons();
        }
    });
}

function bindAnalyzerEvents() {
    const btnCheckScore = document.getElementById('btn-check-score');
    if (!btnCheckScore) return;

    btnCheckScore.addEventListener('click', async () => {
        const fileInput = document.getElementById('score-upload').files[0];
        const jobDesc = document.getElementById('score-job-desc').value;
        
        if (!fileInput || !jobDesc.trim()) {
            showNotification("Please provide both a PDF and a Job Description.", "error");
            return;
        }

        const originalText = btnCheckScore.innerHTML;
        btnCheckScore.innerHTML = '<i data-lucide="loader" class="spin"></i> Analyzing...';
        btnCheckScore.disabled = true;
        lucide.createIcons();

        try {
            const formData = new FormData();
            formData.append('file', fileInput);
            const parseRes = await fetch('http://localhost:5000/parse', { method: 'POST', body: formData });
            const parseData = await parseRes.json();
            if (!parseRes.ok) throw new Error(parseData.error || "Parsing failed");

            const matchData = await analyzeMatch(parseData.extracted_text, jobDesc);
            
            document.getElementById('live-score').innerText = `${matchData.score}%`;
            const missingList = document.getElementById('live-missing');
            missingList.innerHTML = '';
            
            if (matchData.missing_keywords.length === 0) {
                missingList.innerHTML = '<li>Optimal match found.</li>';
            } else {
                matchData.missing_keywords.forEach(kw => {
                    const li = document.createElement('li');
                    li.innerText = kw;
                    missingList.appendChild(li);
                });
            }
            showNotification("Analysis complete", "success");
        } catch (error) {
            showNotification(error.message, "error");
        } finally {
            btnCheckScore.innerHTML = originalText;
            btnCheckScore.disabled = false;
            lucide.createIcons();
        }
    });
}