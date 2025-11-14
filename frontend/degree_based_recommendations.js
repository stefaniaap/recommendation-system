// ============================
// Base API URL
// ============================
const API_BASE = "http://localhost:8000";

// ============================
// Load all universities into the university dropdown
// ============================
async function loadUniversities() {
    const res = await fetch(`${API_BASE}/universities`);
    const data = await res.json();

    const select = document.getElementById("university");
    data.forEach(u => select.appendChild(new Option(u.university_name, u.university_id)));
}

// ============================
// Load degree programs for a selected university
// ============================
async function loadPrograms(univId) {
    const dropdown = document.getElementById('program');
    // Reset dropdown options
    dropdown.innerHTML = '<option value="">-- Select Program --</option>';
    if (!univId) return;

    try {
        const response = await fetch(`${API_BASE}/universities/${univId}/degrees`);
        const degrees = await response.json();

        degrees.forEach(degree => {
            const option = document.createElement('option');
            option.value = degree.program_id;
            option.textContent = `${degree.degree_type}: ${Array.isArray(degree.degree_titles) ? degree.degree_titles.join(', ') : ''}`;
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading degree programs:", error);
    }
}

// ============================
// Load elective skills for a selected university and program
// ============================
async function loadElectiveSkills(univId, programId) {
    const container = document.getElementById("skillsContainer");
    container.innerHTML = "<p>Loading skills...</p>";

    // If university or program is not selected, display message
    if (!univId || !programId) {
        container.innerHTML = "<p>Please select a university and a program first.</p>";
        return;
    }

    // Debug log to inspect request parameters
    console.log("Fetching elective skills for university:", univId, "program:", programId);

    try {
        const res = await fetch(`${API_BASE}/universities/${univId}/degrees/${programId}/elective-skills`);
        if (!res.ok) {
            console.error(`Fetch returned status ${res.status}`);
            container.innerHTML = `<p style="color:red;">Error ${res.status}: Skills not found.</p>`;
            return;
        }
        const data = await res.json();
        container.innerHTML = "";

        // If no skills returned
        if (!data.skills || data.skills.length === 0) {
            container.innerHTML = "<p>No skills available for this program.</p>";
            return;
        }

        // Create checkboxes for each skill
        const content = document.createElement("div");
        content.className = "category-content";

        data.skills.forEach(skill => {
            const label = document.createElement("label");
            label.innerHTML = `<input type="checkbox" value="${skill.skill_id}" data-skill-name="${skill.skill_name}"> ${skill.skill_name}`;
            content.appendChild(label);
        });

        container.appendChild(content);

    } catch (err) {
        console.error("Error loading elective skills:", err);
        container.innerHTML = "<p style='color:red;'>Error while loading skills.</p>";
    }
}

// ============================
// Perform search for recommended elective courses
// based on selected university, program, and skills
// ============================
async function performSearch() {
    const universityId = document.getElementById("university").value;
    const programId = document.getElementById("program").value;
    const skills = Array.from(document.querySelectorAll("input[type='checkbox']:checked"))
        .map(cb => cb.dataset.skillName);

    // Validate all fields are selected
    if (!universityId || !programId || skills.length === 0) {
        alert("Please complete all fields.");
        return;
    }

    const resultsContainer = document.getElementById("resultsContainer");
    resultsContainer.innerHTML = "<p>Loading recommendations...</p>";

    try {
        const response = await fetch(`${API_BASE}/universities/${universityId}/degrees/electives`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                program_id: parseInt(programId),
                target_skills: skills,
                top_n: 10
            })
        });

        const data = await response.json();

        // If no recommended electives returned
        if (!data.recommended_electives || data.recommended_electives.length === 0) {
            resultsContainer.innerHTML = "<p>No recommended elective courses found.</p>";
            return;
        }

        // Display each recommended course as a result card
        resultsContainer.innerHTML = "";
        data.recommended_electives.forEach(course => {
            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <h4>${course.course_name}</h4>
                <p><strong>Score:</strong> ${course.score.toFixed(3)}</p>
                ${course.skills?.length ? `<p><strong>Skills:</strong> ${course.skills.join(', ')}</p>` : ''}
                ${course.matching_skills?.length ? `<p><strong>Matching Skills:</strong> ${course.matching_skills.join(', ')}</p>` : ''}
            `;
            resultsContainer.appendChild(card);
        });

    } catch (err) {
        console.error(err);
        resultsContainer.innerHTML = "<p style='color:red;'>Error fetching recommendations.</p>";
    }
}

// ============================
// Event Listeners
// ============================
document.addEventListener("DOMContentLoaded", () => {
    // Load universities on page load
    loadUniversities();

    // Load programs when a university is selected
    document.getElementById("university").addEventListener("change", e => loadPrograms(e.target.value));

    // Load skills when a program is selected
    document.getElementById("program").addEventListener("change", e => {
        const univId = document.getElementById("university").value;
        const programId = e.target.value;
        loadElectiveSkills(univId, programId);
    });

    // Trigger search on button click
    document.getElementById("searchBtn").addEventListener("click", performSearch);
});
