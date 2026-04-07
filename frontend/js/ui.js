function switchTab(tab, event) {
  const sections = ["builder", "match"];

  sections.forEach(id => {
    document.getElementById(id).classList.add("hidden");
  });

  document.getElementById(tab).classList.remove("hidden");
  
  // Update active state for sidebar buttons
  const buttons = document.querySelectorAll('.sidebar-btn');
  buttons.forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Set active button
  event.target.closest('.sidebar-btn').classList.add('active');
}