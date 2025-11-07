
// === Δυναμικό API_BASE_PATH ανάλογα με το περιβάλλον ===
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'http://api:8000';

// =======================================================
// 1. Βοηθητική Συνάρτηση Χρωμάτων
// =======================================================
function scoreToCourseColor(score) {
    const clampedScore = Math.max(0, Math.min(1, score));
    const lowR = 198, lowG = 226, lowB = 189; // Light Green
    const highR = 40, highG = 167, highB = 69; // Green (Success)
    const r = Math.round(lowR + (highR - lowR) * clampedScore);
    const g = Math.round(lowG + (highG - lowG) * clampedScore);
    const b = Math.round(lowB + (highB - lowB) * clampedScore);
    return `rgb(${r}, ${g}, ${b})`;
}

// =======================================================
// 2. Συνάρτηση Heatmap Δεξιοτήτων
// =======================================================
function generateSkillsHeatmap(skills) {
    if (!skills || skills.length === 0) {
        return `<p style="color: #6c757d; font-size: 0.9em;">Δεν βρέθηκαν συσχετισμένες δεξιότητες.</p>`;
    }

    return skills.slice(0, 5).map(skill => {
        const skillScore = skill.skill_score || 0;
        const width = Math.round(skillScore * 100);
        const barColor = scoreToCourseColor(skillScore);
        return `
            <div class="skill-bar">
                <p style="margin:0; font-size:0.85em;">
                    ${skill.skill_name} 
                    <span style="font-weight: 600; color: ${barColor};">${width}%</span>
                </p>
                <div class="bar-wrap">
                    <div class="bar" style="width: ${width}%; background-color: ${barColor};"></div>
                </div>
            </div>
        `;
    }).join('');
}

// =======================================================
// 3. Συνάρτηση Εμφάνισης Μαθημάτων
// =======================================================
function displayCourseRecommendations(courses, degreeName) {
    const resultsContainer = document.getElementById('course-recommendation-list');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (loadingSpinner) loadingSpinner.style.display = 'none';
    if (titleElement) titleElement.textContent = `📚 Προτεινόμενα Μαθήματα για το: ${decodeURIComponent(degreeName)}`;

    if (!resultsContainer) return;

    if (!courses || courses.length === 0) {
        resultsContainer.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">
            ❌ Δεν βρέθηκαν προτεινόμενα μαθήματα.
        </li>`;
        return;
    }

    let htmlContent = '';

    courses.forEach(course => {
        const score = course.score ? course.score.toFixed(3) : 'N/A';
        const color = scoreToCourseColor(course.score || 0);

        const description = course.description || 'Δεν βρέθηκε.';
        const objectives = course.objectives || 'Δεν βρέθηκαν.';
        const learning_outcomes = course.learning_outcomes || 'Δεν βρέθηκαν.';
        const course_content = course.course_content || 'Δεν βρέθηκε.';

        const newSkills = (course.new_skills || []).map(s => `<span class="badge bg-success me-1">${s}</span>`).join(' ');
        const compatibleSkills = (course.compatible_skills || []).map(s => `<span class="badge bg-info me-1">${s}</span>`).join(' ');

        // Heatmap HTML
        const heatmapHTML = generateSkillsHeatmap(course.skill_details || []);

        htmlContent += `
            <li class="course-card" style="border-left-color: ${color};">
                <div class="card-header">
                    <p class="course-name">${course.course_name || 'Άγνωστο Μάθημα'}</p>
                    <div class="score-badge" style="background-color: ${color};">
                        Score: ${score}
                    </div>
                </div>

                <div class="info-grid mt-3">
                    <div class="info-item">
                        <h6>🎯 Σκοπός/Στόχοι</h6>
                        <p>${objectives.substring(0, 150)}...</p>
                    </div>
                    <div class="info-item">
                        <h6>💡 Μαθησιακά Αποτελέσματα</h6>
                        <p>${learning_outcomes.substring(0, 150)}...</p>
                    </div>
                </div>

                <div class="info-section mt-3 p-3" style="border: 1px dashed #ced4da; background-color: #f7f7f7;">
                    <h6>🌐 Περίληψη Περιγραφής</h6>
                    <p style="font-size: 0.85em;">${description.substring(0, 200)}...</p>
                    <details>
                        <summary style="cursor: pointer; color: #007bff; font-weight: 500; margin-top: 10px;">Πλήρης Ανάλυση & Skills</summary>
                        <h6 class="mt-2">Πλήρης Περιγραφή</h6>
                        <p style="font-size: 0.8em;">${description}</p>
                        <h6 class="mt-2">Περιεχόμενο Μαθήματος</h6>
                        <p style="font-size: 0.8em;">${course_content}</p>
                        <h6 class="mt-2">✅ Νέες Δεξιότητες</h6>
                        <p>${newSkills || 'Καμία νέα δεξιότητα.'}</p>
                        <h6 class="mt-2">🔗 Συμβατές Δεξιότητες</h6>
                        <p>${compatibleSkills || 'Καμία συμβατή δεξιότητα.'}</p>
                        <h6 class="mt-2">📊 Heatmap Δεξιοτήτων</h6>
                        ${heatmapHTML}
                    </details>
                </div>
            </li>
        `;
    });

    resultsContainer.innerHTML = htmlContent;
}

// =======================================================
// 4. Φόρτωση Δεδομένων από API
// =======================================================
async function fetchAndDisplayRecommendations() {
    const headerElement = document.getElementById('courses-header');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');
    const listElement = document.getElementById('course-recommendation-list');

    if (!headerElement || !titleElement || !loadingSpinner || !listElement) {
        console.error("Ένα ή περισσότερα DOM στοιχεία είναι null.");
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    const degreeName = params.get('degree_name');

    if (!univId || !degreeName) {
        headerElement.textContent = `Σφάλμα: Δεδομένα URL ελλιπή.`;
        titleElement.textContent = "";
        loadingSpinner.style.display = 'none';
        return;
    }

    const decodedDegreeName = decodeURIComponent(degreeName);

    // Φόρτωση ονόματος πανεπιστημίου
    let univName = `Πανεπιστήμιο ID: ${univId}`;
    try {
        const univsResponse = await fetch(`${API_BASE_URL}/universities`);
        if (univsResponse.ok) {
            const universities = await univsResponse.json();
            const targetUniv = universities.find(u => String(u.university_id) === univId);
            if (targetUniv) univName = targetUniv.university_name;
        }
    } catch (error) {
        console.warn("Could not fetch university name:", error);
    }

    headerElement.textContent = `Πανεπιστήμιο: ${univName}`;
    titleElement.textContent = `Φόρτωση Μαθημάτων για ${decodedDegreeName}...`;
    loadingSpinner.style.display = 'block';

    // Κλήση API
    const endpoint = `${API_BASE_URL}/recommend/courses/${univId}/${degreeName}`;
    console.log("Calling API URL:", endpoint);

    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            let errorDetail = await response.text();
            try { errorDetail = JSON.parse(errorDetail).detail || errorDetail; } catch { }
            throw new Error(`HTTP error! Status: ${response.status}. Detail: ${errorDetail}`);
        }
        const data = await response.json();
        const recommendations = data.recommendations || [];
        displayCourseRecommendations(recommendations, degreeName);
    } catch (error) {
        console.error("Σφάλμα φόρτωσης προτεινόμενων μαθημάτων:", error);
        loadingSpinner.style.display = 'none';
        listElement.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">
            Αποτυχία φόρτωσης δεδομένων: ${error.message}.
        </li>`;
    }
}

// Εκκίνηση
fetchAndDisplayRecommendations();

