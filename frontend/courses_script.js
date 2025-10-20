// =======================================================
// courses_script.js (ΤΕΛΙΚΗ ΕΚΔΟΣΗ ΜΕ ΜΠΛΕ ΧΡΩΜΑΤΑ)
// =======================================================

const API_BASE_URL = 'http://127.0.0.1:8000';

// =======================================================
// 1. Βοηθητική Συνάρτηση Χρωμάτων (ΤΩΡΑ ΣΕ ΜΠΛΕ)
// =======================================================

function scoreToCourseColor(score) {
    const clampedScore = Math.max(0, Math.min(1, score));

    // Χαμηλό σκορ (Πολύ ανοιχτό γαλάζιο/μπλε)
    const lowR = 200, lowG = 220, lowB = 255;

    // Υψηλό σκορ (Έντονο μπλε/Primary color)
    const highR = 23, highG = 100, highB = 200;

    // Υπολογισμός παρεμβολής για το heatmap
    const r = Math.round(lowR + (highR - lowR) * clampedScore);
    const g = Math.round(lowG + (highG - lowG) * clampedScore);
    const b = Math.round(lowB + (highB - lowB) * clampedScore);

    return `rgb(${r}, ${g}, ${b})`;
}


// =======================================================
// 2. Συνάρτηση Εμφάνισης Μαθημάτων
// =======================================================

function displayCourseRecommendations(courses, degreeName) {
    const resultsContainer = document.getElementById('course-recommendation-list');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    loadingSpinner.style.display = 'none';

    titleElement.textContent = `📚 Προτεινόμενα Μαθήματα για το: ${decodeURIComponent(degreeName)}`;

    // Χειρισμός μηδενικών αποτελεσμάτων
    if (!courses || !Array.isArray(courses) || courses.length === 0) {
        resultsContainer.innerHTML = `<li style="color: #dc3545; padding: 20px; background: #fff;">❌ Δεν βρέθηκαν προτεινόμενα μαθήματα για αυτό το πτυχίο ή δεν υπάρχουν παρόμοια για σύγκριση.</li>`;
        return;
    }

    const htmlContent = courses.map(course => {
        const score = course.score ? course.score.toFixed(3) : 'N/A';
        // Χρησιμοποιούμε τη νέα, μπλε συνάρτηση χρωμάτων
        const color = scoreToCourseColor(course.score || 0);

        return `
            <li class="course-item-card" style="border-left-color: ${color};">
                <p class="course-name">${course.course_name || 'Άγνωστο Μάθημα'}</p>
                <div class="course-score" style="background-color: ${color};">
                    Score: ${score}
                </div>
            </li>
        `;
    }).join('');

    resultsContainer.innerHTML = htmlContent;
}


// =======================================================
// 3. Κύρια Συνάρτηση Φόρτωσης
// =======================================================

async function loadCourseRecommendations() {
    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    const degreeName = params.get('degree_name');

    const infoElement = document.getElementById('degree-info');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (!univId || !degreeName) {
        infoElement.innerHTML = "Σφάλμα: Δεν βρέθηκαν τα απαραίτητα δεδομένα (univ_id ή degree_name) στο URL.";
        loadingSpinner.style.display = 'none';
        return;
    }

    const decodedDegreeName = decodeURIComponent(degreeName);

    infoElement.textContent = `Πανεπιστήμιο ID: ${univId} | Πτυχίο: ${decodedDegreeName}`;
    document.getElementById('courses-title').textContent = `Φόρτωση Μαθημάτων...`;
    loadingSpinner.style.display = 'block';

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

        // Εξασφαλίζουμε ότι το recommendations είναι array
        const recommendations = data.recommendations || [];

        displayCourseRecommendations(recommendations, degreeName);

    } catch (error) {
        console.error("Σφάλμα φόρτωσης προτεινόμενων μαθημάτων:", error);
        loadingSpinner.style.display = 'none';
        document.getElementById('course-recommendation-list').innerHTML =
            `<li style="color: #dc3545; padding: 20px; background: #fff;">Αποτυχία φόρτωσης δεδομένων: ${error.message}. Ελέγξτε αν ο FastAPI server τρέχει.</li>`;
    }
}

// Εκκίνηση της διαδικασίας με τη φόρτωση της σελίδας
document.addEventListener('DOMContentLoaded', loadCourseRecommendations);