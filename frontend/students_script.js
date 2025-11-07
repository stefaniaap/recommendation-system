// ===============================
// students_script.js
// ===============================

// ✅ Προσαρμόσμένο για το backend σου (χωρίς αλλαγές στο main.py)
const API_BASE = "http://127.0.0.1:8000";

// ------------------------------------------------------------
// 🔹 Φόρτωση όλων των δεξιοτήτων (grouped)
// ------------------------------------------------------------
async function loadSkills() {
    try {
        const response = await fetch(`${API_BASE}/skills/grouped-by-categories`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const data = await response.json();
        console.log("Loaded grouped skills:", data);

        const container = document.getElementById("skillsContainer");
        container.innerHTML = "";

        // ✅ Αν το response είναι αντικείμενο (όχι array)
        if (typeof data === "object" && !Array.isArray(data)) {
            Object.keys(data).forEach(category => {
                const catDiv = document.createElement("div");
                catDiv.className = "skill-category";
                catDiv.innerHTML = `<h4>${category}</h4>`;

                const skills = data[category];
                skills.forEach(skill => {
                    const label = document.createElement("label");
                    label.innerHTML = `
                        <input type="checkbox" value="${skill.id}" data-skill-name="${skill.name}">
                        ${skill.name}
                    `;
                    catDiv.appendChild(label);
                });

                container.appendChild(catDiv);
            });
        } else {
            console.warn("Unexpected skill data format:", data);
        }

    } catch (error) {
        console.error("Error loading skills:", error);
    }
}

// ------------------------------------------------------------
// 🔹 Αναζήτηση (με χρήση /recommend/personalized)
// ------------------------------------------------------------
async function performSearch() {
    const selectedSkills = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(cb => cb.getAttribute("data-skill-name"));

    if (selectedSkills.length === 0) {
        alert("❗ Επέλεξε τουλάχιστον μία δεξιότητα.");
        return;
    }
    const language = document.getElementById("language").value || null;
    const country = document.getElementById("country").value || null;
    const degree_type = document.getElementById("degreeType").value || null;


    const payload = {
        target_skills: selectedSkills,
        language,
        country,
        degree_type
    };

    try {
        const response = await fetch(`${API_BASE}/recommend/personalized`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const data = await response.json();
        console.log("Search results:", data);

        displayResults(data);

    } catch (error) {
        console.error("Error performing search:", error);
        alert("⚠️ Παρουσιάστηκε σφάλμα κατά την αναζήτηση.");
    }
}

// ------------------------------------------------------------
// 🔹 Εμφάνιση Αποτελεσμάτων
// ------------------------------------------------------------
function displayResults(data) {
    const resultsContainer = document.getElementById("resultsContainer");
    resultsContainer.innerHTML = "";

    if (!data || (!data.recommended_programs && !data.recommended_unlinked_courses)) {
        resultsContainer.innerHTML = "<p>Δεν βρέθηκαν αποτελέσματα.</p>";
        return;
    }

    // Προγράμματα σπουδών
    if (data.recommended_programs && data.recommended_programs.length > 0) {
        const progDiv = document.createElement("div");
        progDiv.innerHTML = "<h3>🎓 Προτεινόμενα Προγράμματα</h3>";

        data.recommended_programs.forEach(p => {
            const item = document.createElement("div");
            item.className = "result-item";
            item.innerHTML = `
                <strong>${p.degree_name}</strong> (${p.degree_type || "N/A"})<br>
                Πανεπιστήμιο: ${p.university || "—"}<br>
                Χώρα: ${p.country || "—"}<br>
                Γλώσσα: ${p.language || "—"}<br>
                Βαθμολογία: ${p.score}
            `;
            progDiv.appendChild(item);
        });
        resultsContainer.appendChild(progDiv);
    }

    // Μαθήματα
    if (data.recommended_unlinked_courses && data.recommended_unlinked_courses.length > 0) {
        const courseDiv = document.createElement("div");
        courseDiv.innerHTML = "<h3>📘 Ανεξάρτητα Μαθήματα</h3>";

        data.recommended_unlinked_courses.forEach(c => {
            const item = document.createElement("div");
            item.className = "result-item";
            item.innerHTML = `
                <strong>${c.lesson_name}</strong><br>
                Πανεπιστήμιο: ${c.university || "—"}<br>
                Βαθμολογία: ${c.score}
            `;
            courseDiv.appendChild(item);
        });
        resultsContainer.appendChild(courseDiv);
    }
}

// ------------------------------------------------------------
// 🔹 Εκκίνηση
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    loadSkills();
    document.getElementById("searchBtn").addEventListener("click", performSearch);
});
