// ======================================================
// Base API URL for backend endpoints
// ======================================================
const API_BASE = "http://localhost:8000";

// ======================================================
// Load dropdown filters for degree type, country, language
// ======================================================
async function loadFilters() {
    try {
        // Fetch degree types and populate dropdown
        const degrees = await fetch(`${API_BASE}/filters/degree-types`).then(r => r.json());
        degrees.forEach(d => document.getElementById("degreeType").appendChild(new Option(d, d)));

        // Fetch countries and populate dropdown
        const countries = await fetch(`${API_BASE}/filters/countries`).then(r => r.json());
        countries.forEach(c => document.getElementById("country").appendChild(new Option(c, c)));

        // Fetch languages and populate dropdown
        const languages = await fetch(`${API_BASE}/filters/languages`).then(r => r.json());
        languages.forEach(l => document.getElementById("language").appendChild(new Option(l, l)));
    } catch (err) {
        console.error("Error loading filters:", err);
    }
}

// ======================================================
// Load skills grouped by categories and create collapsible sections
// ======================================================
async function loadSkills() {
    try {
        const data = await fetch(`${API_BASE}/skills/grouped-by-categories`).then(r => r.json());
        const container = document.getElementById("skillsContainer");
        container.innerHTML = "";

        // Iterate over each skill category
        Object.keys(data).forEach(cat => {
            const catDiv = document.createElement("div");
            catDiv.className = "skill-category";

            // Category header with collapsible icon
            const header = document.createElement("div");
            header.className = "category-header";
            header.innerHTML = `<span>${cat.toUpperCase()}</span> <i class="fas fa-chevron-down"></i>`;
            catDiv.appendChild(header);

            // Container for skills within the category
            const content = document.createElement("div");
            content.className = "category-content";

            // Create checkbox for each skill
            data[cat].forEach(skill => {
                const label = document.createElement("label");
                label.innerHTML = `<input type="checkbox" value="${skill.id}" data-skill-name="${skill.name}"> ${skill.name}`;
                content.appendChild(label);
            });

            catDiv.appendChild(content);
            container.appendChild(catDiv);

            // Toggle visibility when header is clicked
            header.addEventListener("click", () => {
                const isVisible = content.style.display === "grid";
                content.style.display = isVisible ? "none" : "grid";
                header.classList.toggle("active", !isVisible);
                header.querySelector("i").classList.toggle("fa-chevron-down", isVisible);
                header.querySelector("i").classList.toggle("fa-chevron-up", !isVisible);
            });
        });
    } catch (err) {
        console.error("Error loading skills:", err);
    }
}

// ======================================================
// Create a circular progress indicator for recommendation scores
// ======================================================
function createCircularProgress(score) {
    const radius = 35;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;

    const svgNS = "http://www.w3.org/2000/svg";

    // Create SVG container
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", "80");
    svg.setAttribute("height", "80");

    // Background circle
    const bg = document.createElementNS(svgNS, "circle");
    bg.setAttribute("cx", "40");
    bg.setAttribute("cy", "40");
    bg.setAttribute("r", radius);
    bg.setAttribute("class", "bg");

    // Progress circle (dynamic stroke offset)
    const progress = document.createElementNS(svgNS, "circle");
    progress.setAttribute("cx", "40");
    progress.setAttribute("cy", "40");
    progress.setAttribute("r", radius);
    progress.setAttribute("class", "progress");
    progress.style.strokeDasharray = circumference;
    progress.style.strokeDashoffset = offset;

    // Text in the center of the circle
    const text = document.createElementNS(svgNS, "text");
    text.setAttribute("x", "40");
    text.setAttribute("y", "45");
    text.textContent = `${score}%`;

    // Append elements to SVG
    svg.appendChild(bg);
    svg.appendChild(progress);
    svg.appendChild(text);

    // Wrap SVG in a container div
    const wrapper = document.createElement("div");
    wrapper.className = "circular-progress";
    wrapper.appendChild(svg);

    return wrapper;
}

// ======================================================
// Display recommendation results in the UI
// ======================================================
function displayResults(data) {
    const container = document.getElementById("results");
    container.innerHTML = "";

    // If no recommendations, show a message
    if (!data || (!data.recommended_programs && !data.recommended_unlinked_courses)) {
        container.innerHTML = "<p style='padding:20px;text-align:center;color:#6c757d;'>No recommendations found based on your selected criteria.</p>";
        return;
    }

    // Function to create a single result card
    const createCard = (title, meta, extra, score) => {
        const card = document.createElement("div");
        card.className = "result-card";

        // Clean title from unwanted characters
        const cleanTitle = title.replace(/[[\]"']+/g, '');

        const infoDiv = document.createElement("div");
        infoDiv.className = "card-info";
        infoDiv.innerHTML = `
            <div class="card-title">${cleanTitle}</div>
            <div class="card-meta">${meta}</div>
            <div class="card-extra">${extra}</div>
        `;

        card.appendChild(infoDiv);
        card.appendChild(createCircularProgress(score));

        return card;
    };

    // Render Recommended Programs
    if (data.recommended_programs?.length) {
        const div = document.createElement("div");
        div.innerHTML = "<h3>Recommended Programs</h3>";

        data.recommended_programs.forEach(p => {
            let score = (p.score || 0) * 100;
            score = Math.max(1, Math.min(score, 100));
            score = Math.round(score);

            if (score < 20) return; // Filter out scores below 20%

            const meta = `Type: ${p.degree_type || "N/A"}`;
            const extra = `University: ${p.university || "—"} | Country: ${p.country || "—"} | Language: ${p.language || "—"}`;
            div.appendChild(createCard(p.degree_name, meta, extra, score));
        });

        container.appendChild(div);
    }

    // Render Independent Courses
    if (data.recommended_unlinked_courses?.length) {
        const div = document.createElement("div");
        div.innerHTML = "<h3>📘 Independent Courses</h3>";

        data.recommended_unlinked_courses.forEach(c => {
            let score = (c.score || 0) * 100;
            score = Math.max(1, Math.min(score, 100));
            score = Math.round(score);

            if (score < 20) return; // Filter out scores below 20%

            const meta = `Provider: ${c.provider || "N/A"}`;
            const extra = `University: ${c.university || "—"}`;
            div.appendChild(createCard(c.lesson_name, meta, extra, score));
        });

        container.appendChild(div);
    }
}

// ======================================================
// Perform personalized search based on selected skills and filters
// ======================================================
async function performSearch() {
    // Gather selected skills
    const selectedSkills = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(cb => cb.dataset.skillName);

    // Build request payload
    const payload = {
        target_skills: selectedSkills,
        degree_type: document.getElementById("degreeType").value || null,
        country: document.getElementById("country").value || null,
        language: document.getElementById("language").value || null
    };

    try {
        const data = await fetch(`${API_BASE}/recommend/personalized`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(r => r.json());

        displayResults(data);
    } catch (err) {
        console.error("Error fetching personalized recommendations:", err);
        alert("⚠️ Error fetching results");
    }
}

// ======================================================
// Initialize page on DOMContentLoaded
// ======================================================
document.addEventListener("DOMContentLoaded", () => {
    loadFilters();  // Load dropdown filter options
    loadSkills();   // Load skill categories
    document.getElementById("searchBtn").addEventListener("click", performSearch); // Bind search button
});
