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
async function loadElectiveSkills(univId, programId, semester) {
    const container = document.getElementById("skillsContainer");
    container.innerHTML = "<p>Loading skills...</p>";

    if (!univId || !programId || !semester) {
        container.innerHTML = "<p>Please select a university, a program, and a semester.</p>";
        return;
    }

    console.log("Fetching elective skills:", { univId, programId, semester });

    try {
        const res = await fetch(
            `${API_BASE}/universities/${univId}/degrees/${programId}/elective-skills?semester=${semester}`
        );

        if (!res.ok) {
            console.error(`Fetch returned status ${res.status}`);
            container.innerHTML = `<p style="color:red;">Error ${res.status}: Skills not found.</p>`;
            return;
        }

        const data = await res.json();
        container.innerHTML = "";

        if (!data.skills || data.skills.length === 0) {
            container.innerHTML = "<p>No skills for this semester.</p>";
            return;
        }

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



async function loadSemesters(univId, programId) {
    // Έλεγξε αν το dropdown υπάρχει
    const dropdown = document.getElementById("semester");
    if (!dropdown) {
        console.error("Dropdown element with id 'semester' not found!");
        return;
    }

    // Καθαρισμός dropdown
    dropdown.innerHTML = '<option value="">-- Select Semester --</option>';

    // Έλεγχος παραμέτρων
    if (!univId || !programId) {
        console.warn("University ID or Program ID is missing:", univId, programId);
        return;
    }

    try {
        console.log(`Fetching semesters for university: ${univId}, program: ${programId}`);
        const res = await fetch(`${API_BASE}/universities/${univId}/degrees/${programId}/semesters`);

        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        const data = await res.json();

        console.log("API response:", data);

        if (!data.semesters || data.semesters.length === 0) {
            console.warn("No semesters returned from API.");
            return;
        }

        data.semesters.forEach(sem => {
            console.log("Adding semester to dropdown:", sem);
            dropdown.appendChild(new Option(sem, sem));
        });

        console.log("Dropdown populated successfully.");

    } catch (err) {
        console.error("Error loading semesters:", err);
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

        const semester = document.getElementById("semester").value;
        const response = await fetch(`${API_BASE}/universities/${universityId}/degrees/electives?semester=${semester}`, {
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
                ${course.website ? `<p><strong>Website:</strong> <a href="${course.website}" target="_blank" class="course-link">${course.website}</a></p>` : ''}
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

    // Load universities initially
    loadUniversities();

    const univDropdown = document.getElementById("university");
    const programDropdown = document.getElementById("program");
    const semesterDropdown = document.getElementById("semester");

    // When university changes → load programs
    univDropdown.addEventListener("change", () => {
        const univId = univDropdown.value;

        loadPrograms(univId);

        // Clear semester & skills
        semesterDropdown.innerHTML = '<option value="">-- Select Semester --</option>';
        document.getElementById("skillsContainer").innerHTML = "";
    });

    // When program changes → load semesters
    programDropdown.addEventListener("change", () => {
        const univId = univDropdown.value;
        const programId = programDropdown.value;

        if (univId && programId) {
            loadSemesters(univId, programId);
        }

        // Clear skills
        document.getElementById("skillsContainer").innerHTML = "";
    });

    // When semester changes → load elective skills
    semesterDropdown.addEventListener("change", () => {
        const univId = univDropdown.value;
        const programId = programDropdown.value;
        const semester = semesterDropdown.value;

        loadElectiveSkills(univId, programId, semester);
    });

    // Search button
    document.getElementById("searchBtn").addEventListener("click", performSearch);
});
