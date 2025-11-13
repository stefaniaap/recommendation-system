const API_BASE = "http://localhost:8000";

async function loadUniversities() {
    const res = await fetch(`${API_BASE}/universities`);
    const data = await res.json();
    const select = document.getElementById("university");
    data.forEach(u => select.appendChild(new Option(u.university_name, u.university_id)));
}

async function loadPrograms(univId) {
    const dropdown = document.getElementById('program');
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
        console.error("Error loading degrees:", error);
    }
}

async function loadElectiveSkills(univId, programId) {
    const container = document.getElementById("skillsContainer");
    container.innerHTML = "<p>Φόρτωση δεξιοτήτων...</p>";

    if (!univId || !programId) {
        container.innerHTML = "<p>Επιλέξτε πανεπιστήμιο και πρόγραμμα πρώτα.</p>";
        return;
    }

    // ✅ Debug log για να βλέπουμε τι στέλνουμε
    console.log("Fetching elective skills for university:", univId, "program:", programId);

    try {
        const res = await fetch(`${API_BASE}/universities/${univId}/degrees/${programId}/elective-skills`);
        if (!res.ok) {
            console.error(`Fetch returned status ${res.status}`);
            container.innerHTML = `<p style="color:red;">Σφάλμα ${res.status}: Δεν βρέθηκαν δεξιότητες.</p>`;
            return;
        }
        const data = await res.json();
        container.innerHTML = "";

        if (!data.skills || data.skills.length === 0) {
            container.innerHTML = "<p>Δεν υπάρχουν δεξιότητες για το πρόγραμμα.</p>";
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
        container.innerHTML = "<p style='color:red;'>Σφάλμα κατά τη φόρτωση δεξιοτήτων.</p>";
    }
}

async function performSearch() {
    const universityId = document.getElementById("university").value;
    const programId = document.getElementById("program").value;
    const skills = Array.from(document.querySelectorAll("input[type='checkbox']:checked")).map(cb => cb.dataset.skillName);

    if (!universityId || !programId || skills.length === 0) {
        alert("Παρακαλώ συμπληρώστε όλα τα πεδία.");
        return;
    }

    const resultsContainer = document.getElementById("resultsContainer");
    resultsContainer.innerHTML = "<p>Φόρτωση συστάσεων...</p>";

    try {
        const response = await fetch(`${API_BASE}/universities/${universityId}/degrees/electives`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ program_id: parseInt(programId), target_skills: skills, top_n: 10 })
        });
        const data = await response.json();

        if (!data.recommended_electives || data.recommended_electives.length === 0) {
            resultsContainer.innerHTML = "<p>Δεν βρέθηκαν προτεινόμενα μαθήματα επιλογής.</p>";
            return;
        }

        resultsContainer.innerHTML = "";
        data.recommended_electives.forEach(course => {
            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
        <h4> ${course.course_name}</h4>
        <p><strong>Score:</strong> ${course.score.toFixed(3)}</p>
        ${course.skills?.length ? `<p><strong>Δεξιότητες:</strong> ${course.skills.join(', ')}</p>` : ''}
        ${course.matching_skills?.length ? `<p><strong>Συμβατές δεξιότητες:</strong> ${course.matching_skills.join(', ')}</p>` : ''}
    `;
            resultsContainer.appendChild(card);
        });


    } catch (err) {
        console.error(err);
        resultsContainer.innerHTML = "<p style='color:red;'>Σφάλμα κατά την ανάκτηση συστάσεων.</p>";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadUniversities();
    document.getElementById("university").addEventListener("change", e => loadPrograms(e.target.value));
    document.getElementById("program").addEventListener("change", e => {
        const univId = document.getElementById("university").value;
        const programId = e.target.value;
        loadElectiveSkills(univId, programId);
    });
    document.getElementById("searchBtn").addEventListener("click", performSearch);
});