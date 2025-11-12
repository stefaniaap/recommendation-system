const API_BASE_URL = 'http://api:8000';

// ---------------------------
// Load Degree Types, Countries, Languages
// ---------------------------
async function loadFilters() {
    try {
        // Degree Types
        const resDegrees = await fetch(`${API_BASE}/filters/degree-types`);
        const degrees = await resDegrees.json();
        const degreeSelect = document.getElementById("degreeType");
        degrees.forEach(d => {
            const opt = document.createElement("option");
            opt.value = d;
            opt.textContent = d;
            degreeSelect.appendChild(opt);
        });

        // Countries
        const resCountries = await fetch(`${API_BASE}/filters/countries`);
        const countries = await resCountries.json();
        const countrySelect = document.getElementById("country");
        countries.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c;
            opt.textContent = c;
            countrySelect.appendChild(opt);
        });

        // Languages
        const resLanguages = await fetch(`${API_BASE}/filters/languages`);
        const languages = await resLanguages.json();
        const languageSelect = document.getElementById("language");
        languages.forEach(l => {
            const opt = document.createElement("option");
            opt.value = l;
            opt.textContent = l;
            languageSelect.appendChild(opt);
        });
    } catch (err) {
        console.error("Error loading filters:", err);
    }
}

// ---------------------------
// Load Skills
// ---------------------------
async function loadSkills() {
    try {
        const res = await fetch(`${API_BASE}/skills/grouped-by-categories`);
        const data = await res.json();
        const container = document.getElementById("skillsContainer");
        container.innerHTML = "";

        if (typeof data === "object" && !Array.isArray(data)) {
            Object.keys(data).forEach(cat => {
                const catDiv = document.createElement("div");
                catDiv.className = "skill-category";
                catDiv.innerHTML = `<h4>${cat}</h4>`;
                data[cat].forEach(skill => {
                    const label = document.createElement("label");
                    label.innerHTML = `<input type="checkbox" value="${skill.id}" data-skill-name="${skill.name}"> ${skill.name}`;
                    catDiv.appendChild(label);
                });
                container.appendChild(catDiv);
            });
        }
    } catch (err) {
        console.error("Error loading skills:", err);
    }
}

// ---------------------------
// Perform Search
// ---------------------------
async function performSearch() {
    const selectedSkills = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(cb => cb.getAttribute("data-skill-name"));

    if (selectedSkills.length === 0) {
        alert("❗ Please select at least one skill.");
        return;
    }

    const payload = {
        target_skills: selectedSkills,
        degree_type: document.getElementById("degreeType").value || null,
        country: document.getElementById("country").value || null,
        language: document.getElementById("language").value || null
    };

    try {
        const res = await fetch(`${API_BASE}/recommend/personalized`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        displayResults(data);
    } catch (err) {
        console.error("Search error:", err);
        alert("⚠️ Error occurred during search.");
    }
}

// ---------------------------
// Display Results
// ---------------------------
function displayResults(data) {
    const container = document.getElementById("results");
    container.innerHTML = "";

    if (!data || (!data.recommended_programs && !data.recommended_unlinked_courses)) {
        container.innerHTML = "<p>No results found.</p>";
        return;
    }

    if (data.recommended_programs && data.recommended_programs.length > 0) {
        const div = document.createElement("div");
        div.innerHTML = "<h3>🎓 Recommended Programs</h3>";
        data.recommended_programs.forEach(p => {
            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <div class="card-title">${p.degree_name}</div>
                <div class="card-meta">Type: ${p.degree_type || "N/A"}</div>
                University: ${p.university || "—"}<br>
                Country: ${p.country || "—"}<br>
                Language: ${p.language || "—"}<br>
                Score: ${p.score || 0}
            `;
            div.appendChild(card);
        });
        container.appendChild(div);
    }

    if (data.recommended_unlinked_courses && data.recommended_unlinked_courses.length > 0) {
        const div = document.createElement("div");
        div.innerHTML = "<h3>📘 Independent Courses</h3>";
        data.recommended_unlinked_courses.forEach(c => {
            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <div class="card-title">${c.lesson_name}</div>
                University: ${c.university || "—"}<br>
                Score: ${c.score || 0}
            `;
            div.appendChild(card);
        });
        container.appendChild(div);
    }
}

// ---------------------------
// INIT
// ---------------------------
document.addEventListener("DOMContentLoaded", () => {
    loadFilters();
    loadSkills();
    document.getElementById("searchBtn").addEventListener("click", performSearch);
});
