export const updateDashboardUI = (data) => {
    if (!data) return;

    // Update Score with a slight animation
    const scoreEl = document.getElementById('match-score');
    scoreEl.innerText = `${data.score}%`;
    scoreEl.style.transform = "scale(1.1)";
    setTimeout(() => scoreEl.style.transform = "scale(1)", 200);

    // Update missing keywords
    const missingList = document.getElementById('missing-keywords');
    missingList.innerHTML = '';
    data.missing_keywords.forEach(keyword => {
        const li = document.createElement('li');
        li.innerText = keyword;
        missingList.appendChild(li);
    });
};