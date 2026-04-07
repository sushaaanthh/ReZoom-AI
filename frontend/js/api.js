async function uploadResume() {
  const file = document.getElementById("fileInput").files[0];

  if (!file) {
    alert("Upload a file first");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("http://127.0.0.1:5000/parse", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  document.getElementById("resumeInput").value = data.text || "";
}

async function match() {
  const resume = document.getElementById("resumeInput").value;
  const job = document.getElementById("jobInput").value;

  const res = await fetch("http://127.0.0.1:5000/match", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({resume, job})
  });

  const data = await res.json();

  document.getElementById("score").innerText = "Match Score: " + data.score + "%";
  document.getElementById("keywords").innerText =
    "Missing: " + data.missing.join(", ");
}

async function getSuggestions() {
  const resume = document.getElementById("resumeInput").value;
  const job = document.getElementById("jobInput").value;

  const res = await fetch("http://127.0.0.1:5000/suggest", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({resume, job})
  });

  const data = await res.json();

  document.getElementById("suggestions").innerText =
    data.suggestions.join("\n");
}

async function generatePDF() {
  const name = document.getElementById("name").value;
  const skills = document.getElementById("skills").value;
  const experience = document.getElementById("experience").value;
  const education = document.getElementById("education").value;

  if (!name || !skills) {
    alert("Please fill in at least your name and skills");
    return;
  }

  const res = await fetch("http://127.0.0.1:5000/generate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name, skills, experience, education})
  });

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "resume.pdf";
  a.click();
}