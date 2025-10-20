const API_BASE_URL = 'http://127.0.0.1:8000';

// =======================================================
// 1. Βοηθητικές Συναρτήσεις 
// =======================================================

// Βοηθητική συνάρτηση για τη μετατροπή του score σε χρώμα heatmap
function scoreToColor(score) {
    const clampedScore = Math.max(0, Math.min(1, score));
    const lowR = 224, lowG = 242, lowB = 247;
    const highR = 33, highG = 150, highB = 243;

    const r = Math.round(lowR + (highR - lowR) * clampedScore);
    const g = Math.round(lowG + (highG - lowG) * clampedScore);
    const b = Math.round(lowB + (highB - lowB) * clampedScore);

    return `rgb(${r}, ${g}, ${b})`;
}

// Βοηθητική συνάρτηση για τη δημιουργία του Heatmap HTML
function generateSkillsHeatmap(topSkills) {
    if (!topSkills || topSkills.length === 0) {
        return `<p style="color: #6c757d; font-size: 0.9em; margin-top: 5px;">Δε βρέθηκαν συσχετισμένες δεξιότητες.</p>`;
    }

    return topSkills.slice(0, 5).map(skill => {
        const skillScore = skill.skill_score || 0;
        const width = Math.round(skillScore * 100);
        const barColor = scoreToColor(skillScore);

        return `
            <div class="skill-bar">
                <p>
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
// 2. ΝΕΑ Συναρτήση: Χειρισμός Κλικ για ΝΕΑ ΣΕΛΙΔΑ
// =======================================================

function handleRecommendCoursesClick(event) {
    const button = event.target;
    const universityId = button.getAttribute('data-univ-id');
    const degreeName = button.getAttribute('data-degree-name');

    // Κωδικοποιούμε το όνομα του πτυχίου για να είναι ασφαλές στο URL
    const encodedDegreeName = encodeURIComponent(degreeName);

    // Ανακατεύθυνση σε νέα σελίδα
    window.location.href = `courses.html?univ_id=${universityId}&degree_name=${encodedDegreeName}`;
}


// =======================================================
// 3. displayRecommendations (ΑΦΑΙΡΟΥΜΕ τα περιττά πεδία)
// =======================================================

/**
 * Εμφανίζει τις προτάσεις στο HTML.
 * @param {Array<Object>} recommendations - Η λίστα των προτάσεων.
 * @param {string} type - Ο τύπος της πρότασης ('degrees' ή 'courses').
 * @param {string} univId - Το ID του πανεπιστημίου.
 * @param {Object} [profilesMap={}] - Χάρτης των πλήρων προφίλ για τα νέα πεδία.
 */
function displayRecommendations(recommendations, type, univId, profilesMap = {}) {
    const resultsContainer = document.getElementById('recommendation-list');
    const titleElement = document.getElementById('results-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    loadingSpinner.style.display = 'none';

    // Ενημέρωση τίτλου για τον τύπο courses
    let typeTitle = '';
    if (type === 'degrees') {
        typeTitle = 'Πτυχίων/Προγραμμάτων (βάσει Skills)';
    } else if (type === 'courses') {
        typeTitle = 'Πιθανών Νέων Πτυχίων (Course Based)';
    }

    if (!recommendations || !Array.isArray(recommendations) || recommendations.length === 0 || (recommendations.length === 1 && recommendations[0].info)) {
        resultsContainer.innerHTML = `<li style="color: #dc3545; padding: 20px; background: #fff;">❌ Δεν βρέθηκαν νέες προτάσεις ${typeTitle} για αυτό το Πανεπιστήμιο.</li>`;
        return;
    }

    const htmlContent = recommendations.map((rec, index) => {
        const itemName = rec.degree || rec.degree_title || rec.course_name || 'Άγνωστο Πρόγραμμα';

        let score, degreeType, itemColor;
        let showButton = true;
        let skillsHtml = '';
        let coursesList = '';

        // ❌ ΑΦΑΙΡΕΣΗ: ΔΕΝ ΧΡΕΙΑΖΟΝΤΑΙ ΠΛΕΟΝ ΤΑ ΠΛΗΡΗ ΠΕΔΙΑ ΕΔΩ
        // (Ο χάρτης profilesMap πλέον δεν χρησιμοποιείται σε αυτό το display)

        if (type === 'degrees') {
            // Λογική για suggest_degrees_with_skills
            score = rec.score ? rec.score.toFixed(3) : 'N/A';
            degreeType = rec.degree_type || 'BSc/BA';
            itemColor = scoreToColor(rec.score || 0);
            skillsHtml = generateSkillsHeatmap(rec.top_skills);

        } else if (type === 'courses') {
            // Λογική για suggest_new_degree_proposals 
            const topCourses = rec.suggested_courses ? rec.suggested_courses.slice(0, 5) : [];
            degreeType = 'Proposal';
            score = 'N/A';
            itemColor = '#28a745';
            showButton = true;

            coursesList = topCourses.map(c =>
                `<span class="course-tag">${c.course} (${c.freq})</span>`
            ).join('');
        }


        let degreeSpecificContent = '';
        if (showButton) {
            degreeSpecificContent = `
                <div class="card-content-full-width">
                    
                    ${type === 'degrees' ?
                    `<div class="heatmap-section-full">
                                <h5>Top Associated Skills</h5>
                                ${skillsHtml}
                            </div>` :
                    `<div class="course-list-section">
                                <h5>Suggested Core Courses</h5>
                                <p class="course-tags-wrapper">${coursesList}</p>
                            </div>`
                }

                    <div class="action-section-centered">
                        <button class="recommend-courses-btn" 
                                data-degree-name="${itemName}"
                                data-univ-id="${univId}">
                            Suggest Courses (Νέα Σελίδα)
                        </button>
                    </div>
                </div>
            `;
        }


        return `
            <li class="recommendation-item recommendation-card" style="border-left-color: ${itemColor};">
                <div class="card-header">
                    <div class="degree-info">
                        <h4 class="degree-name">${itemName} <span class="degree-type">[${degreeType}]</span></h4>
                    </div>
                    
                    <div class="score-badge" style="background-color: ${itemColor};">
                        ${type === 'courses' ? 'Proposal' : `Score: ${score}`}
                    </div>
                </div>
                
                ${degreeSpecificContent}

            </li>
        `;
    }).join('');

    titleElement.textContent = `📊 Προτεινόμενα ${typeTitle} (${recommendations.length})`;
    resultsContainer.innerHTML = htmlContent;

    // ΠΡΟΣΘΗΚΗ EVENT LISTENERS ΓΙΑ ΤΟ ΝΕΟ ΚΛΙΚ
    document.querySelectorAll('.recommend-courses-btn').forEach(button => {
        button.addEventListener('click', handleRecommendCoursesClick);
    });
}


// =======================================================
// 4. Κύρια Συνάρτηση: loadRecommendations (Απλοποίηση)
// =======================================================

async function loadRecommendations() {
    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    const type = params.get('type');

    const infoElement = document.getElementById('university-info');
    const titleElement = document.getElementById('results-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (!univId || !type) {
        infoElement.textContent = "Σφάλμα: Δεν βρέθηκε αναγνωριστικό Πανεπιστημίου (univ_id) στο URL.";
        loadingSpinner.style.display = 'none';
        return;
    }

    // 1. Βρίσκουμε το όνομα του πανεπιστημίου για τον τίτλο
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
        console.error("Error fetching universities:", error);
    }
    infoElement.textContent = `Τρέχουσα Ανάλυση: ${univName}`;
    titleElement.textContent = `Φόρτωση Προτάσεων ${type === 'degrees' ? 'Πτυχίων' : 'Νέων Προγραμμάτων'}...`;


    // 2. Κάνουμε την κλήση στο API
    loadingSpinner.style.display = 'block';
    let apiUrl = '';

    if (type === 'degrees') {
        // http://127.0.0.1:8000/recommend/degrees/1
        apiUrl = `${API_BASE_URL}/recommend/degrees/${univId}`;
    } else if (type === 'courses') {
        // http://127.0.0.1:8000/recommendations/university/1 (Αυτό το endpoint επιστρέφει new_degree_proposals)
        apiUrl = `${API_BASE_URL}/recommendations/university/${univId}`;
    } else {
        infoElement.textContent = "Σφάλμα: Άγνωστος τύπος αναζήτησης.";
        loadingSpinner.style.display = 'none';
        return;
    }

    // ❌ ΑΦΑΙΡΕΣΗ ΤΗΣ ΔΕΥΤΕΡΗΣ ΚΛΗΣΗΣ /profiles/{univId}
    // Αφού τα πεδία δεν εμφανίζονται, δεν χρειάζεται να τα ζητήσουμε.

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // 3. Εμφάνιση αποτελεσμάτων
        let recommendationsToShow;
        if (type === 'degrees') {
            // Το endpoint /recommend/degrees/{id} επιστρέφει ένα αντικείμενο με 'recommended_degrees'
            recommendationsToShow = data.recommended_degrees || [];
        } else if (type === 'courses') {
            // Το endpoint /recommendations/university/{id} επιστρέφει ένα αντικείμενο με 'recommendations'
            recommendationsToShow = data.recommendations.new_degree_proposals || [];
        }

        // 4. Εμφανίζουμε μόνο τις βασικές προτάσεις.
        // Το profilesMap δεν χρειάζεται πλέον.
        displayRecommendations(recommendationsToShow, type, univId);

    } catch (error) {
        console.error("Fetch error:", error);
        document.getElementById('recommendation-list').innerHTML =
            `<li style="color: #dc3545; padding: 20px; background: #fff;">
                 ⚠️ Αδυναμία φόρτωσης δεδομένων. Βεβαιωθείτε ότι ο FastAPI server είναι σε λειτουργία.
             </li>`;
        titleElement.textContent = "Σφάλμα Φόρτωσης Αποτελεσμάτων";
        loadingSpinner.style.display = 'none';
    }
}

// Εκκίνηση της φόρτωσης όταν η σελίδα είναι έτοιμη
document.addEventListener('DOMContentLoaded', loadRecommendations);