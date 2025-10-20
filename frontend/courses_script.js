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
// 2. Συνάρτηση Εμφάνισης Μαθημάτων (ΜΕ ΟΜΑΔΟΠΟΙΗΣΗ) 💡
// =======================================================

function displayCourseRecommendations(courses, degreeName) {
    const resultsContainer = document.getElementById('course-recommendation-list');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    loadingSpinner.style.display = 'none';
    titleElement.textContent = `📚 Προτεινόμενα Μαθήματα για το: ${decodeURIComponent(degreeName)}`;

    if (!courses || !Array.isArray(courses) || courses.length === 0) {
        resultsContainer.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">
            ❌ Δεν βρέθηκαν προτεινόμενα μαθήματα για αυτό το πτυχίο ή δεν υπάρχουν παρόμοια για σύγκριση.
        </li>`;
        return;
    }

    // 1. ΟΜΑΔΟΠΟΙΗΣΗ: Χρησιμοποιούμε την πρώτη "ΝΕΑ" δεξιότητα ως κλειδί
    const groupedBySkill = courses.reduce((acc, course) => {
        // Επιλογή της πιο σημαντικής δεξιότητας (πρώτη νέα δεξιότητα)
        const groupKey = course.new_skills && course.new_skills.length > 0
            ? `Νέος Τομέας: ${course.new_skills[0]}`
            : 'Γενικές Συστάσεις (Ενίσχυση)'; // Fallback

        if (!acc[groupKey]) {
            acc[groupKey] = [];
        }
        acc[groupKey].push(course);
        return acc;
    }, {});


    // 2. ΔΗΜΙΟΥΡΓΙΑ HTML ανά ΟΜΑΔΑ
    let htmlContent = '';

    for (const groupKey in groupedBySkill) {
        const groupCourses = groupedBySkill[groupKey];

        // Τίτλος Ομάδας
        htmlContent += `<h3 class="section-title mt-5" style="color: #007bff;">${groupKey} (${groupCourses.length} Μαθήματα)</h3>`;

        // Λίστα Μαθημάτων
        groupCourses.forEach(course => {
            const score = course.score ? course.score.toFixed(3) : 'N/A';
            const color = scoreToCourseColor(course.score || 0);

            // 🚨 ΝΕΑ ΠΕΔΙΑ ΠΕΡΙΓΡΑΦΗΣ (με fallback)
            const description = course.description || 'Δεν βρέθηκε.';
            const objectives = course.objectives || 'Δεν βρέθηκαν.';
            const learning_outcomes = course.learning_outcomes || 'Δεν βρέθηκαν.';
            const course_content = course.course_content || 'Δεν βρέθηκε.';

            // Μετατροπή των skills σε badges
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
// 3. Κύρια Συνάρτηση Φόρτωσης
// =======================================================

async function loadCourseRecommendations() {
    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    const degreeName = params.get('degree_name');

    const headerElement = document.getElementById('courses-header');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (!univId || !degreeName) {
        headerElement.textContent = "Σφάλμα: Δεδομένα URL ελλιπή.";
        loadingSpinner.style.display = 'none';
        return;
    }

    const decodedDegreeName = decodeURIComponent(degreeName);

    // 1. Φόρτωση ονόματος πανεπιστημίου
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

    headerElement.textContent = `Πανεπιστήμιο: ${univName}`;
    document.getElementById('courses-title').textContent = `Φόρτωση Μαθημάτων για ${decodedDegreeName}...`;
    loadingSpinner.style.display = 'block';

    // 2. Κλήση API
    const endpoint = `${API_BASE_URL}/recommend/courses/${univId}/${degreeName}`;

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

        // 🚨 ΚΑΛΟΥΜΕ τη διορθωμένη συνάρτηση εμφάνισης με ομαδοποίηση
        displayCourseRecommendations(recommendations, degreeName);

    } catch (error) {
        console.error("Σφάλμα φόρτωσης προτεινόμενων μαθημάτων:", error);
        loadingSpinner.style.display = 'none';
        document.getElementById('course-recommendation-list').innerHTML =
            `<li class="course-card" style="border-left-color: #dc3545;">Αποτυχία φόρτωσης δεδομένων: ${error.message}. Ελέγξτε αν ο FastAPI server τρέχει.</li>`;
    }
}

// Εκκίνηση της διαδικασίας με τη φόρτωση της σελίδας
document.addEventListener('DOMContentLoaded', loadCourseRecommendations);