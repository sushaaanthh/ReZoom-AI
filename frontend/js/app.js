import { parsePDF, optimizeResume, analyzeMatch, generatePDF } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme(); 
    initializeNavigation(); 
    initializeTemplateSelection();
    bindMakerEvents(); 
    bindOptimizerEvents(); 
    bindAnalyzerEvents();
    
    document.getElementById('add-edu-btn').addEventListener('click', () => addEducation());
    document.getElementById('add-exp-btn').addEventListener('click', () => addExperience());
    document.getElementById('add-proj-btn').addEventListener('click', () => addProject());
    document.getElementById('add-skill-btn').addEventListener('click', () => addTechSkill());

    addEducation(); addExperience(); addProject(); addTechSkill();
});

function initializeNavigation() {
    const tabs = document.querySelectorAll('.nav-icon');
    const contents = document.querySelectorAll('.tab-content');
    const rightPanel = document.getElementById('analytics-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const targetId = tab.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
            if (targetId === 'tab-score') rightPanel.classList.remove('hidden');
            else rightPanel.classList.add('hidden');
        });
    });
}

function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    if(themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            const isLight = document.body.classList.contains('light-mode');
            themeIcon.setAttribute('data-lucide', isLight ? 'moon' : 'sun');
            lucide.createIcons();
        });
    }
}

function initializeTemplateSelection() {
    window.selectedTemplate = 'classic';
    document.querySelectorAll('.template-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.template-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            window.selectedTemplate = card.getAttribute('data-template');
        });
    });
}

function addEducation(data = {}) {
    const id = Date.now();
    const html = `
    <div class="dynamic-item glass-panel mt-2" id="edu-${id}" style="padding: 15px;">
        <div style="display: flex; justify-content: space-between;"><h5>Education</h5><button class="btn-secondary" style="padding: 5px 10px;" onclick="document.getElementById('edu-${id}').remove()">X</button></div>
        <div class="grid-2-col mt-2">
            <input type="text" class="edu-uni" placeholder="University Name" value="${data.university || ''}">
            <input type="text" class="edu-degree" placeholder="Degree / Specialization" value="${data.degree || ''}">
            <input type="text" class="edu-city" placeholder="City" value="${data.city || ''}">
            <input type="text" class="edu-country" placeholder="Country" value="${data.country || ''}">
            <input type="text" class="edu-grades" placeholder="Grades" value="${data.grades || ''}">
            <div style="display: flex; gap: 10px;">
                <input type="text" class="edu-start" placeholder="Start" value="${data.start || ''}">
                <input type="text" class="edu-end" placeholder="End" value="${data.end || ''}">
            </div>
        </div>
    </div>`;
    document.getElementById('education-container').insertAdjacentHTML('beforeend', html);
}

function addExperience(data = {}) {
    const id = Date.now();
    const html = `
    <div class="dynamic-item glass-panel mt-2" id="exp-${id}" style="padding: 15px;">
        <div style="display: flex; justify-content: space-between;"><h5>Experience</h5><button class="btn-secondary" style="padding: 5px 10px;" onclick="document.getElementById('exp-${id}').remove()">X</button></div>
        <input type="text" class="exp-company mt-2" placeholder="Company / Role" value="${data.company || ''}">
        <div style="display: flex; gap: 10px;" class="mt-2">
            <input type="text" class="exp-start" placeholder="Start" value="${data.start || ''}">
            <input type="text" class="exp-end" placeholder="End" value="${data.end || ''}">
        </div>
        <textarea class="exp-desc mt-2" rows="3" placeholder="Description / Responsibilities">${data.description || ''}</textarea>
    </div>`;
    document.getElementById('experience-container').insertAdjacentHTML('beforeend', html);
}

function addProject(data = {}) {
    const id = Date.now();
    const html = `
    <div class="dynamic-item glass-panel mt-2" id="proj-${id}" style="padding: 15px;">
        <div style="display: flex; justify-content: space-between;"><h5>Project</h5><button class="btn-secondary" style="padding: 5px 10px;" onclick="document.getElementById('proj-${id}').remove()">X</button></div>
        <input type="text" class="proj-name mt-2" placeholder="Project Name" value="${data.name || ''}">
        <textarea class="proj-desc mt-2" rows="2" placeholder="Project Description">${data.description || ''}</textarea>
    </div>`;
    document.getElementById('projects-container').insertAdjacentHTML('beforeend', html);
}

function addTechSkill(data = {}) {
    const id = Date.now();
    const html = `
    <div class="dynamic-item glass-panel mt-2" id="skill-${id}" style="padding: 15px;">
        <div style="display: flex; justify-content: space-between;"><h5>Skill Category</h5><button class="btn-secondary" style="padding: 5px 10px;" onclick="document.getElementById('skill-${id}').remove()">X</button></div>
        <div class="grid-2-col mt-2">
            <input type="text" class="skill-type" placeholder="Category" value="${data.type || ''}">
            <input type="text" class="skill-list" placeholder="Skills (Comma separated)" value="${data.skills || ''}">
        </div>
    </div>`;
    document.getElementById('tech-skills-container').insertAdjacentHTML('beforeend', html);
}

function gatherFormData() {
    const getVals = (containerId, selectors, keys) => {
        return Array.from(document.getElementById(containerId).children).map(item => {
            let obj = {};
            selectors.forEach((sel, i) => obj[keys[i]] = item.querySelector(sel).value);
            return obj;
        });
    };

    return {
        name: document.getElementById('maker-name').value,
        email: document.getElementById('maker-email').value,
        phone: document.getElementById('maker-phone').value,
        linkedin: document.getElementById('maker-linkedin').value,
        summary: document.getElementById('maker-summary').value,
        education: getVals('education-container', ['.edu-uni', '.edu-degree', '.edu-city', '.edu-country', '.edu-grades', '.edu-start', '.edu-end'], ['university', 'degree', 'city', 'country', 'grades', 'start', 'end']),
        experience: getVals('experience-container', ['.exp-company', '.exp-desc', '.exp-start', '.exp-end'], ['company', 'description', 'start', 'end']),
        projects: getVals('projects-container', ['.proj-name', '.proj-desc'], ['name', 'description']),
        tech_skills: getVals('tech-skills-container', ['.skill-type', '.skill-list'], ['type', 'skills']),
        soft_skills: document.getElementById('maker-soft-skills').value ? document.getElementById('maker-soft-skills').value.split(',').map(s=>s.trim()) : [],
        template: window.selectedTemplate || 'classic'
    };
}

// THE DOWNLOAD FIXES ARE HERE
function triggerDownload(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link); // Fixes the browser block
    link.click();
    document.body.removeChild(link); // Cleans up the invisible link
}

function bindMakerEvents() {
    const makerUpload = document.getElementById('maker-upload');
    const btnExportMaker = document.getElementById('btn-export-maker');

    if (makerUpload) {
        makerUpload.addEventListener('change', async (e) => {
            if (!e.target.files[0]) return;
            const formData = new FormData(); formData.append('file', e.target.files[0]);
            try {
                const response = await parsePDF(formData);
                const data = response.data;
                
                document.getElementById('maker-name').value = data.name || "";
                document.getElementById('maker-email').value = data.email || "";
                document.getElementById('maker-phone').value = data.phone || "";
                document.getElementById('maker-linkedin').value = data.linkedin || "";
                document.getElementById('maker-summary').value = data.summary || "";
                document.getElementById('maker-soft-skills').value = (data.soft_skills || []).join(", ");

                document.getElementById('education-container').innerHTML = '';
                (data.education || []).forEach(edu => addEducation(edu));
                
                document.getElementById('experience-container').innerHTML = '';
                (data.experience || []).forEach(exp => addExperience(exp));

                document.getElementById('projects-container').innerHTML = '';
                (data.projects || []).forEach(proj => addProject(proj));

                document.getElementById('tech-skills-container').innerHTML = '';
                (data.tech_skills || []).forEach(skill => addTechSkill(skill));
            } catch (error) { alert("Parsing Error: " + error.message); }
        });
    }

    if (btnExportMaker) {
        btnExportMaker.addEventListener('click', async () => {
            const payload = gatherFormData();
            const btnOriginal = btnExportMaker.innerHTML;
            btnExportMaker.innerHTML = "Generating PDF...";
            try {
                const response = await generatePDF(payload);
                if (response.download_url) triggerDownload(response.download_url, 'ReZoom_Resume.pdf');
            } catch (error) { alert("Generation Error: " + error.message); }
            finally { btnExportMaker.innerHTML = btnOriginal; }
        });
    }
}

function bindOptimizerEvents() {
    const btnOptimize = document.getElementById('btn-optimize');
    if(btnOptimize) {
        btnOptimize.addEventListener('click', async () => {
            const fileInput = document.getElementById('match-upload').files[0];
            const jobDesc = document.getElementById('match-job-desc').value;
            if (!fileInput) return alert("Upload a PDF");
            
            const btnOriginal = btnOptimize.innerHTML;
            btnOptimize.innerHTML = "Optimizing...";
            
            const formData = new FormData(); formData.append('file', fileInput);
            try {
                const parseRes = await parsePDF(formData);
                const optRes = await optimizeResume({ parsed_resume: parseRes.data, job_description: jobDesc });
                
                let finalPayload = parseRes.data;
                // Strict mapping so arrays don't get erased
                finalPayload.experience = optRes.data.experience || finalPayload.experience;
                finalPayload.tech_skills = optRes.data.tech_skills || finalPayload.tech_skills;
                finalPayload.soft_skills = optRes.data.soft_skills || finalPayload.soft_skills;
                finalPayload.template = 'classic'; 
                
                const genRes = await generatePDF(finalPayload);
                document.getElementById('match-results').classList.remove('hidden');
                document.getElementById('btn-export-match').onclick = () => {
                    triggerDownload(genRes.download_url, 'Optimized_Resume.pdf');
                };
            } catch(error) { alert(error.message); }
            finally { btnOptimize.innerHTML = btnOriginal; }
        });
    }
}

function bindAnalyzerEvents() {
    const btnCheckScore = document.getElementById('btn-check-score');
    if(btnCheckScore) {
        btnCheckScore.addEventListener('click', async () => {
            const fileInput = document.getElementById('score-upload').files[0];
            const jobDesc = document.getElementById('score-job-desc').value;
            if (!fileInput) return alert("Upload a PDF");

            const btnOriginal = btnCheckScore.innerHTML;
            btnCheckScore.innerHTML = "Analyzing...";

            const formData = new FormData(); formData.append('file', fileInput);
            try {
                const parseData = await parsePDF(formData);
                const matchData = await analyzeMatch(JSON.stringify(parseData.data), jobDesc, fileInput.name);
                
                document.getElementById('live-score').innerText = `${matchData.score || 0}%`;
                
                const missingKws = matchData.missing_keywords || [];
                document.getElementById('live-missing').innerHTML = missingKws.length > 0 
                    ? missingKws.map(kw => `<li>${kw}</li>`).join('') 
                    : `<li>No critical keywords missing!</li>`;
                
                const violations = matchData.rule_violations || [];
                document.getElementById('live-violations').innerHTML = violations.length > 0
                    ? violations.map(rule => `<li>${rule}</li>`).join('')
                    : `<li style="color: #2ecc71;">Perfect ATS Formatting!</li>`;
                    
            } catch(error) { alert("Analysis Error: " + error.message); }
            finally { btnCheckScore.innerHTML = btnOriginal; }
        });
    }
}