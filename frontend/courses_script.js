// === ΔΙΟΡΘΩΣΗ: Δυναμικό API_BASE_PATH ανάλογα με το περιβάλλον ===
const API_BASE_URL = 'http://127.0.0.1:8000';
// =======================================================
// 1. Βοηθητική Συνάρτηση Χρωμάτων
// =======================================================

function scoreToCourseColor(score) {
    const clampedScore = Math.max(0, Math.min(1, score));
    // Χρώμα: Από ανοιχτό πράσινο προς σκούρο πράσινο (συνάφεια)
    const lowR = 198, lowG = 226, lowB = 189; // Light Green
    const highR = 40, highG = 167, highB = 69; // Green (Success)

    const r = Math.round(lowR + (highR - lowR) * clampedScore);
    const g = Math.round(lowG + (highR - lowG) * clampedScore);
    const b = Math.round(lowB + (highR - lowB) * clampedScore);

    return `rgb(${r}, ${g}, ${b})`;
}


// =======================================================
// 2. Συνάρτηση Εμφάνισης Μαθημάτων
// =======================================================

function displayCourseRecommendations(courses, degreeName) {
    const resultsContainer = document.getElementById('course-recommendation-list');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (loadingSpinner) loadingSpinner.style.display = 'none';
    if (titleElement) titleElement.textContent = `📚 Recommended Courses for: ${decodeURIComponent(degreeName)}`;

    if (!resultsContainer) {
        console.error("Κρίσιμο Σφάλμα: Missing #course-recommendation-list.");
        return;
    }

    if (!courses || !Array.isArray(courses) || courses.length === 0) {
        resultsContainer.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">
            ❌ Δεν βρέθηκαν προτεινόμενα μαθήματα για αυτό το πτυχίο ή δεν υπάρχουν παρόμοια για σύγκριση.
        </li>`;
        return;
    }

    // ΟΜΑΔΟΠΟΙΗΣΗ
    const groupedBySkill = courses.reduce((acc, course) => {
        const groupKey = course.new_skills && course.new_skills.length > 0
            ? `Νέος Τομέας: ${course.new_skills[0]}`
            : 'Γενικές Συστάσεις (Ενίσχυση)';

        if (!acc[groupKey]) {
            acc[groupKey] = [];
        }
        acc[groupKey].push(course);
        return acc;
    }, {});


    // ΔΗΜΙΟΥΡΓΙΑ HTML
    let htmlContent = '';

    for (const groupKey in groupedBySkill) {
        const groupCourses = groupedBySkill[groupKey];

        htmlContent += `<h3 class="section-title mt-5" style="color: #007bff;">${groupKey} (${groupCourses.length} Μαθήματα)</h3>`;

        groupCourses.forEach(course => {
            const score = course.score ? course.score.toFixed(3) : 'N/A';
            const color = scoreToCourseColor(course.score || 0);

            // Ασφαλής ανάκτηση πεδίων (για να αποφεύγονται τα 'null')
            const description = course.description || 'Δεν βρέθηκε.';
            const objectives = course.objectives || 'Δεν βρέθηκαν.';
            const learning_outcomes = course.learning_outcomes || 'Δεν βρέθηκαν.';
            const course_content = course.course_content || 'Δεν βρέθηκε.';

            const newSkills = (course.new_skills || []).map(s => `<span class="badge bg-success me-1">${s}</span>`).join(' ');
            const compatibleSkills = (course.compatible_skills || []).map(s => `<span class="badge bg-info me-1">${s}</span>`).join(' ');

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
                        </details>
                    </div>
                </li>
            `;
        });
    }

    resultsContainer.innerHTML = htmlContent;
}


// =======================================================
// 3. Κύριες Συνάρτησεις Φόρτωσης (ΜΕ ΔΙΑΓΝΩΣΤΙΚΟΥΣ ΕΛΕΓΧΟΥΣ)
// =======================================================

async function fetchAndDisplayRecommendations() {
    // 1. Ασφαλής ανάκτηση DOM στοιχείων (Debug check)
    const headerElement = document.getElementById('courses-header');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');
    const listElement = document.getElementById('course-recommendation-list');

    // **ΔΙΑΓΝΩΣΤΙΚΟΣ ΚΩΔΙΚΑΣ (DEBUGGING)**
    // Ο έλεγχος για null αποτρέπει το σφάλμα "Cannot set properties of null"
    if (headerElement === null || titleElement === null || loadingSpinner === null || listElement === null) {
        console.error("ΔΙΑΓΝΩΣΗ ΣΦΑΛΜΑΤΟΣ: Ένα ή περισσότερα DOM στοιχεία είναι null. Βεβαιωθείτε ότι το HTML σας περιέχει τα ID: 'courses-header', 'courses-title', 'loading-spinner', 'course-recommendation-list'.");
        return;
    }

    // 2. Λήψη παραμέτρων URL
    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    const degreeName = params.get('degree_name'); // Αυτό έρχεται κωδικοποιημένο από το results_script.js

    if (!univId || !degreeName) {
        headerElement.textContent = `Σφάλμα: Δεδομένα URL ελλιπή.`;
        titleElement.textContent = "";
        loadingSpinner.style.display = 'none';
        return;
    }

    const decodedDegreeName = decodeURIComponent(degreeName);

    // 3. Φόρτωση ονόματος πανεπιστημίου
    let univName = `Πανεπιστήμιο ID: ${univId}`;
    try {
        const univsResponse = await fetch(`${API_BASE_URL}/universities`);
        if (univsResponse.ok) {
            const universities = await univsResponse.json();
            const targetUniv = universities.find(u => String(u.university_id) === univId);
            if (targetUniv) {
                univName = targetUniv.university_name;
            }
        }
    } catch (error) {
        console.warn("Could not fetch university name:", error);
    }

    // Ενημέρωση των header/title
    headerElement.textContent = `Πανεπιστήμιο: ${univName}`;
    titleElement.textContent = `Φόρτωση Μαθημάτων για ${decodedDegreeName}...`;
    loadingSpinner.style.display = 'block';

    // 4. Κλήση API (Χρησιμοποιεί το κωδικοποιημένο degreeName)
    //const endpoint = `${API_BASE_URL}/recommend/courses/${univId}/${degreeName}`;
    const endpoint = `${API_BASE_URL}/recommend/courses/${univId}/${encodeURIComponent(degreeName)}`;

    console.log("Calling API URL:", endpoint);

    try {
        const response = await fetch(endpoint);

        let data;
        if (!response.ok) {
            let errorDetail = await response.text();
            try {
                const errorJson = JSON.parse(errorDetail);
                errorDetail = errorJson.detail || errorDetail;
            } catch (e) {
                // ignore
            }
            throw new Error(`HTTP error! Status: ${response.status}. Detail: ${errorDetail}`);
        }

        data = await response.json();
        const recommendations = data.recommendations || [];

        displayCourseRecommendations(recommendations, degreeName);

    } catch (error) {
        console.error("Σφάλμα φόρτωσης προτεινόμενων μαθημάτων:", error);

        loadingSpinner.style.display = 'none';

        listElement.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">Αποτυχία φόρτωσης δεδομένων: ${error.message}. Ελέγξτε αν ο FastAPI server τρέχει.</li>`;
    }
}

// Εκκίνηση της διαδικασίας
fetchAndDisplayRecommendations();