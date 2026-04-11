// Removed the broken parsePDF import
import { analyzeMatch, generatePDF } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            document.body.classList.toggle('dark-mode');
            themeIcon.setAttribute('data-lucide', document.body.classList.contains('light-mode') ? 'moon' : 'sun');
            lucide.createIcons();
        });
    }

    // 2. Tab Switching Logic & Panel Visibility
    const navIcons = document.querySelectorAll('.nav-icon');
    const tabContents = document.querySelectorAll('.tab-content');
    const analyticsPanel = document.getElementById('analytics-panel');
    
    // Hide panel by default on load (since Maker is the default tab)
    analyticsPanel.classList.add('hidden');

    navIcons.forEach(icon => {
        icon.addEventListener('click', () => {
            if(!icon.hasAttribute('data-target')) return; // Ignore theme toggle

            // Remove active class from all tabs and icons
            navIcons.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            // Activate the clicked tab
            icon.classList.add('active');
            const targetId = icon.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            // Handle Right Panel Visibility
            if (targetId === 'tab-score') {
                analyticsPanel.classList.remove('hidden');
            } else {
                analyticsPanel.classList.add('hidden');
            }
        });
    });

    // 3. Template Selection Logic
    let selectedTemplate = 'base';
    const tempCards = document.querySelectorAll('.template-card');
    tempCards.forEach(card => {
        card.addEventListener('click', () => {
            tempCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedTemplate = card.getAttribute('data-template');
        });
    });

    // 4. Maker Tab: Auto-fill PDF parsing
    const makerUpload = document.getElementById('maker-upload');
    if(makerUpload) {
        makerUpload.addEventListener('change', async (e) => {
            if(e.target.files[0]) {
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
                    document.getElementById('maker-exp').value = data.extracted_text || "Could not extract text.";
                } catch (error) {
                    alert("Error parsing PDF. Ensure backend is running.");
                }
                
                uploadBox.innerHTML = originalHTML;
                lucide.createIcons();
            }
        });
    }

    // 5. Maker Tab: Export PDF
    const btnExportMaker = document.getElementById('btn-export-maker');
    if(btnExportMaker) {
        btnExportMaker.addEventListener('click', async () => {
            const payload = {
                name: document.getElementById('maker-name').value || "Your Name",
                email: document.getElementById('maker-email').value || "email@example.com",
                education: document.getElementById('maker-edu').value,
                experience: document.getElementById('maker-exp').value,
                skills: document.getElementById('maker-skills').value,
                template: selectedTemplate
            };

            btnExportMaker.innerHTML = '<i data-lucide="loader" class="spin"></i> Generating...';
            lucide.createIcons();

            const response = await generatePDF(payload);
            if(response && response.download_url) {
                alert("PDF Generated! Endpoint returned: " + response.download_url);
            } else {
                alert("Generation failed. Check backend terminal for LaTeX errors.");
            }
            
            btnExportMaker.innerHTML = '<i data-lucide="download"></i> Export as PDF';
            lucide.createIcons();
        });
    }

    // 6. Score Tab: Check Score
    const btnCheckScore = document.getElementById('btn-check-score');
    if(btnCheckScore) {
        btnCheckScore.addEventListener('click', async () => {
            const fileInput = document.getElementById('score-upload').files[0];
            const jobDesc = document.getElementById('score-job-desc').value;
            
            if(!fileInput || !jobDesc) return alert("Please upload a PDF and enter a Job Description.");

            btnCheckScore.innerHTML = '<i data-lucide="loader" class="spin"></i> Analyzing...';
            lucide.createIcons();

            try {
                const formData = new FormData();
                formData.append('file', fileInput);
                const parseRes = await fetch('http://localhost:5000/parse', { method: 'POST', body: formData });
                const parseData = await parseRes.json();

                const matchData = await analyzeMatch(parseData.extracted_text, jobDesc);
                
                document.getElementById('live-score').innerText = `${matchData.score}%`;
                const missingList = document.getElementById('live-missing');
                missingList.innerHTML = '';
                matchData.missing_keywords.forEach(kw => {
                    const li = document.createElement('li');
                    li.innerText = kw;
                    missingList.appendChild(li);
                });
            } catch (error) {
                alert("Analysis failed. Ensure backend is running.");
            }

            btnCheckScore.innerHTML = '<i data-lucide="activity"></i> Analyze Score';
            lucide.createIcons();
        });
    }
});