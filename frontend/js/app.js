document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Logic
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            document.body.classList.toggle('dark-mode');
            
            // Switch Lucide Icon between sun and moon
            if (document.body.classList.contains('light-mode')) {
                themeIcon.setAttribute('data-lucide', 'moon');
            } else {
                themeIcon.setAttribute('data-lucide', 'sun');
            }
            // Re-render icons
            lucide.createIcons();
        });
    }
});
import { analyzeMatch } from './api.js';
import { updateDashboardUI } from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    
    if(analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            const skills = document.getElementById('skills').value;
            const jobDesc = document.getElementById('job-desc').value;
            
            // Show loading state
            analyzeBtn.innerText = "Analyzing...";
            analyzeBtn.style.opacity = "0.7";

            const result = await analyzeMatch(skills, jobDesc);
            updateDashboardUI(result);

            // Restore button
            analyzeBtn.innerText = "Analyze Fit";
            analyzeBtn.style.opacity = "1";
        });
    }
});