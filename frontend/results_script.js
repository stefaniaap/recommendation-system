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
// 2. ΔΙΟΡΘΩΣΗ: Χειρισμός Κλικ για ΝΕΑ ΣΕΛΙΔΑ (με URL encoding)
// =======================================================

function handleRecommendCoursesClick(event) {
    const button = event.target.closest('.recommend-courses-btn');
    if (!button) return;

    const universityId = button.getAttribute('data-univ-id');
    const degreeName = button.getAttribute('data-degree-name');

    if (!universityId || !degreeName) {
        console.error("Missing data-univ-id or data-degree-name attribute on button.");
        return;
    }

    // ⭐ ΚΡΙΣΙΜΗ ΔΙΟΡΘΩΣΗ: Κωδικοποιούμε το όνομα του πτυχίου για να είναι ασφαλές στο URL
    const encodedDegreeName = encodeURIComponent(degreeName);

    // Ανακατεύθυνση σε courses.html με τις κωδικοποιημένες παραμέτρους
    window.location.href = `courses.html?univ_id=${universityId}&degree_name=${encodedDegreeName}`;
}


// =======================================================
// 3. displayRecommendations 
// =======================================================

/**
 * Εμφανίζει τις προτάσεις στο HTML.
 * @param {Array<Object>} recommendations - Η λίστα των προτάσεων.
 * @param {string} type - Ο τύπος της πρότασης ('degrees' ή 'courses').
 * @param {string} univId - Το ID του πανεπιστημίου.
 */
function displayRecommendations(recommendations, type, univId) {
    const resultsContainer = document.getElementById('recommendation-list');
    const titleElement = document.getElementById('results-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (loadingSpinner) loadingSpinner.style.display = 'none';

    // 1. Έλεγχος για κρίσιμα DOM στοιχεία
    if (!resultsContainer || !titleElement || !loadingSpinner) {
        console.error("Missing critical DOM elements in results.html");
        return;
    }

    // 2. Ενημέρωση τίτλου
    let typeTitle = '';
    if (type === 'degrees') {
        typeTitle = 'Πτυχίων/Προγραμμάτων (βάσει Skills)';
    } else if (type === 'courses') {
        typeTitle = 'Πιθανών Νέων Πτυχίων (Course Based)';
    }

    if (!recommendations || !Array.isArray(recommendations) || recommendations.length === 0 || (recommendations.length === 1 && recommendations[0].info)) {
        resultsContainer.innerHTML = `<li style="color: #dc3545; padding: 20px; background: #fff;">❌ Δεν βρέθηκαν νέες προτάσεις ${typeTitle} για αυτό το Πανεπιστήμιο.</li>`;
        titleElement.textContent = `📊 Αποτελέσματα: Δεν βρέθηκαν (${typeTitle})`;
        return;
    }

    // 3. Δημιουργία HTML περιεχομένου
    const htmlContent = recommendations.map((rec, index) => {
        const itemName = rec.degree || rec.degree_title || rec.course_name || 'Άγνωστο Πρόγραμμα';

        let score, degreeType, itemColor;
        let showButton = true;
        let skillsHtml = '';
        let coursesList = '';

        if (type === 'degrees') {
            // Λογική για suggest_degrees_with_skills
            score = rec.score ? rec.score.toFixed(3) : 'N/A';
            degreeType = rec.degree_type || 'BSc/BA';
            itemColor = scoreToColor(rec.score || 0);
            skillsHtml = generateSkillsHeatmap(rec.top_skills);

            // Το data-degree-name πρέπει να είναι un-encoded εδώ
            rec.data_degree_name = rec.degree;

        } else if (type === 'courses') {
            // Λογική για suggest_new_degree_proposals 
            const topCourses = rec.suggested_courses ? rec.suggested_courses.slice(0, 5) : [];
            degreeType = 'Proposal';
            score = 'N/A';
            itemColor = '#28a745';
            showButton = true;

            // Το data-degree-name πρέπει να είναι un-encoded εδώ
            rec.data_degree_name = rec.degree_title;

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
                                data-degree-name="${rec.data_degree_name}"
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

    // 4. ΠΡΟΣΘΗΚΗ EVENT LISTENERS ΓΙΑ ΤΟ ΝΕΟ ΚΛΙΚ
    document.querySelectorAll('.recommend-courses-btn').forEach(button => {
        button.addEventListener('click', handleRecommendCoursesClick);
    });
}


// =======================================================
// 4. Κύρια Συνάρτηση: loadRecommendations
// =======================================================

async function loadRecommendations() {
    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    const type = params.get('type');

    const infoElement = document.getElementById('university-info');
    const titleElement = document.getElementById('results-title');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContainer = document.getElementById('recommendation-list');

    // Έλεγχος για κρίσιμα DOM στοιχεία
    if (!infoElement || !titleElement || !loadingSpinner || !resultsContainer) {
        console.error("Missing critical DOM elements in results.html during load.");
        return;
    }

    if (!univId || !type) {
        infoElement.textContent = "Σφάλμα: Δεν βρέθηκε αναγνωριστικό Πανεπιστημίου ή τύπος αναζήτησης στο URL.";
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
        apiUrl = `${API_BASE_URL}/recommend/degrees/${univId}`;
    } else if (type === 'courses') {
        apiUrl = `${API_BASE_URL}/recommendations/university/${univId}`;
    } else {
        infoElement.textContent = "Σφάλμα: Άγνωστος τύπος αναζήτησης.";
        loadingSpinner.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(apiUrl);
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
        const data = await response.json();

        // 3. Εμφάνιση αποτελεσμάτων
        let recommendationsToShow;
        if (type === 'degrees') {
            recommendationsToShow = data.recommended_degrees || [];
        } else if (type === 'courses') {
            recommendationsToShow = data.recommendations.new_degree_proposals || [];
        }

        displayRecommendations(recommendationsToShow, type, univId);

    } catch (error) {
        console.error("Fetch error:", error);
        resultsContainer.innerHTML =
            `<li style="color: #dc3545; padding: 20px; background: #fff;">
                 ⚠️ Αδυναμία φόρτωσης δεδομένων. Βεβαιωθείτε ότι ο FastAPI server είναι σε λειτουργία. (Λεπτομέρειες: ${error.message})
             </li>`;
        titleElement.textContent = "Σφάλμα Φόρτωσης Αποτελεσμάτων";
        loadingSpinner.style.display = 'none';
    }
}

// Εκκίνηση της φόρτωσης όταν η σελίδα είναι έτοιμη
document.addEventListener('DOMContentLoaded', loadRecommendations);