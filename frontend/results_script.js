// results_script.js (ΤΕΛΙΚΗ & ΛΕΙΤΟΥΡΓΙΚΗ ΕΚΔΟΣΗ)
// =======================================================

const API_BASE_URL = 'http://127.0.0.1:8000';

// =======================================================
// 1. Βοηθητικές Συναρτήσεις 
// =======================================================

// Μετατροπή score σε πράσινο χρώμα (low -> light green, high -> dark green)
// Στην συνάρτηση scoreToColor, παστέλ απόχρωση
function scoreToColor(score) {
    const clampedScore = Math.max(0, Math.min(1, score));
    const lowR = 223, lowG = 246, lowB = 228; // ανοιχτό παστέλ πράσινο
    const highR = 91, highG = 184, highB = 92; // πιο σκούρο παστέλ πράσινο

    const r = Math.round(lowR + (highR - lowR) * clampedScore);
    const g = Math.round(lowG + (highG - lowG) * clampedScore);
    const b = Math.round(lowB + (highB - lowB) * clampedScore);

    return `rgb(${r}, ${g}, ${b})`;
}

// Στην generateSkillsHeatmap, τα bars θα χρησιμοποιούν τη συνάρτηση scoreToColor


// Δημιουργία HTML για τις δεξιότητες με χρωματιστές μπάρες
function generateSkillsHeatmap(topSkills) {
    if (!topSkills || topSkills.length === 0) {
        return `<p style="color: #6c757d; font-size: 0.9em; margin-top: 5px;">Δε βρέθηκαν συσχετισμένες δεξιότητες.</p>`;
    }

    return topSkills.slice(0, 5).map(skill => {
        const skillScore = skill.skill_score || 0; // Παίρνει το score ή 0 αν λείπει
        const width = Math.round(skillScore * 100); // Πλάτος bar σε %
        const barColor = scoreToColor(skillScore);  // Χρώμα bar

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
// 2. Συναρτήση: Χειρισμός Κλικ για ΝΕΑ ΣΕΛΙΔΑ
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
// 3. displayRecommendations (ΔΙΟΡΘΩΜΕΝΗ)
// =======================================================

function displayRecommendations(recommendations, type, univId) {
    const resultsContainer = document.getElementById('recommendation-list');
    const titleElement = document.getElementById('results-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    loadingSpinner.style.display = 'none';

    // Ενημέρωση τίτλου για τον τύπο courses
    let typeTitle = '';
    if (type === 'degrees') {
        typeTitle = 'Recommended Degrees for:';
    } else if (type === 'courses') {
        typeTitle = 'Recommended Degrees for:'; // Εμφανίζουμε τις προτάσεις νέων πτυχίων
    }

    // 🚨 Θωράκιση: Ελέγχουμε αν η recommendations είναι λίστα και έχει στοιχεία.
    if (!recommendations || !Array.isArray(recommendations) || recommendations.length === 0 || (recommendations.length === 1 && recommendations[0].info)) {
        // ΤΙΤΛΟΣ ΧΩΡΙΣ ΑΡΙΘΜΟ
        titleElement.textContent = `📊 No Results Found`;
        resultsContainer.innerHTML = `<li style="color: #dc3545; padding: 20px; background: #fff; border-left: 8px solid #dc3545; font-size: 1.1em;">❌ Δεν βρέθηκαν νέες προτάσεις ${typeTitle} για αυτό το Πανεπιστήμιο.</li>`;
        return;
    }

    const htmlContent = recommendations.map((rec, index) => {
        // Χρησιμοποιούμε degree_title για τις προτάσεις courses (νέα πτυχία)
        const itemName = rec.degree || rec.degree_title || rec.course_name || 'Άγνωστο Πρόγραμμα';

        let score, degreeType, itemColor;
        let showButton = false;
        let skillsHtml = '';
        let coursesList = '';
        let degreeTitleText = itemName;

        if (type === 'degrees') {
            // Λογική για suggest_degrees_with_skills
            score = rec.score ? rec.score.toFixed(3) : 'N/A';
            degreeType = rec.degree_type || 'BSc/BA';
            itemColor = scoreToColor(rec.score || 0); // Χρήση της συνάρτησης scoreToColor
            showButton = true;
            skillsHtml = generateSkillsHeatmap(rec.top_skills);
            degreeTitleText = itemName;

        } else if (type === 'courses') {
            // Λογική για suggest_new_degree_proposals (από recommend/university)
            const topCourses = rec.suggested_courses ? rec.suggested_courses.slice(0, 5) : [];
            degreeType = 'Proposal';
            score = 'N/A';
            itemColor = '#17a2b8'; // Χρώμα του κουμπιού για να ξεχωρίζει
            showButton = true;

            coursesList = topCourses.map(c =>
                `<span class="course-tag">${c.course} (${c.freq})</span>`
            ).join('');
            degreeTitleText = `${itemName} (New Program Proposal)`;
        }


        let degreeSpecificContent = '';
        if (showButton) {
            degreeSpecificContent = `
                <div class="card-content-full-width">
                    
                    ${type === 'degrees' ?
                    `<div class="heatmap-section-full">
                                <h5><i class="fas fa-chart-bar"></i> Top Associated Skills</h5>
                                ${skillsHtml}
                            </div>` :
                    `<div class="course-list-section">
                                <h5><i class="fas fa-tags"></i> Suggested Core Courses</h5>
                                <div class="course-tags-wrapper">${coursesList}</div>
                            </div>`
                }

                    <div class="action-section-centered">
                        <button class="recommend-courses-btn green-btn" 
                                data-degree-name="${itemName}"
                                data-univ-id="${univId}">
                            <i class="fas fa-tasks"></i> Generate Course Recommendations
                        </button>
                    </div>
                </div>
            `;
        }


        return `
            <li class="recommendation-item recommendation-card" style="border-left-color: ${itemColor};">
                <div class="card-header">
                    <div class="degree-info">
                        <h4 class="degree-name">${degreeTitleText} <span class="degree-type">[${degreeType}]</span></h4>
                    </div>
                    
                    <div class="score-badge" style="background-color: ${itemColor};">
                        ${type === 'courses' ? 'Proposal' : `Score: ${score}`}
                    </div>
                </div>
                
                ${degreeSpecificContent}

            </li>
        `;
    }).join('');

    // ΑΛΛΑΓΗ 2: Χρήση του "Recommended Degrees for:"
    titleElement.textContent = `📊 ${type === 'degrees' ? 'Recommended Degrees for:' : 'Recommended Degrees for:'}`;
    resultsContainer.innerHTML = htmlContent;

    // ΠΡΟΣΘΗΚΗ EVENT LISTENERS ΓΙΑ ΤΟ ΝΕΟ ΚΛΙΚ
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

    // Εμφάνιση Spinner στην αρχή
    loadingSpinner.style.display = 'block';

    if (!univId || !type) {
        infoElement.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: University ID or Recommendation Type not found in URL.`;
        loadingSpinner.style.display = 'none';
        return;
    }

    // 1. Βρίσκουμε το όνομα του πανεπιστημίου για τον τίτλο
    let univName = `University ID: ${univId}`;
    try {
        const univsResponse = await fetch(`${API_BASE_URL}/universities`);
        const universities = await univsResponse.json();
        const selectedUniv = universities.find(u => String(u.university_id) === univId);
        if (selectedUniv) {
            univName = `${selectedUniv.university_name} (${selectedUniv.country})`;
        }
    } catch (e) {
        console.error("Could not fetch university name:", e);
    }

    // Ενημέρωση πληροφοριών (Χρήση εικονιδίων για πιο επαγγελματική εμφάνιση)
    // ΑΛΛΑΓΗ 1: Αφαίρεση του "Results for:" από εδώ και προσθήκη <br><br> για κενό
    infoElement.innerHTML = `<i class="fas fa-info-circle"></i> Find the best programs and courses based on your profile.`;
    titleElement.textContent = `Recommended Degrees for: ${univName}`; // Χρήση του νέου τίτλου

    // 2. Εκτελούμε την κλήση API ανάλογα με τον τύπο
    let endpoint = '';
    if (type === 'degrees') {
        endpoint = `${API_BASE_URL}/recommend/degrees/${univId}`;
    } else if (type === 'courses') {
        endpoint = `${API_BASE_URL}/recommendations/university/${univId}`;
    } else {
        infoElement.textContent = "Άγνωστος τύπος σύστασης.";
        loadingSpinner.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            // Χειρισμός σφάλματος HTTP
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
        let recommendations = [];

        if (type === 'degrees') {
            // ΔΙΟΡΘΩΣΗ: Θωράκιση - αν λείπει το recommended_degrees, παίρνουμε κενή λίστα.
            recommendations = data.recommended_degrees || [];
        } else if (type === 'courses') {
            // ΔΙΟΡΘΩΣΗ: Θωράκιση - αν λείπει το data.recommendations ή new_degree_proposals, παίρνουμε κενή λίστα.
            recommendations = (data.recommendations && data.recommendations.new_degree_proposals) || [];
        }

        // Η κλήση είναι τώρα ασφαλής, καθώς το recommendations είναι πάντα Array
        displayRecommendations(recommendations, type, univId);

    } catch (error) {
        console.error(`Σφάλμα φόρτωσης ${type} συστάσεων:`, error);
        loadingSpinner.style.display = 'none';
        titleElement.textContent = `❌ Error Loading Results`;
        document.getElementById('recommendation-list').innerHTML =
            `<li style="color: #dc3545; padding: 20px; background: #fff; border-left: 8px solid #dc3545; font-size: 1.1em;">
                <i class="fas fa-server"></i> Αποτυχία φόρτωσης δεδομένων: ${error.message}. Ελέγξτε αν ο FastAPI server τρέχει.
            </li>`;
    } finally {
        // Τέλος φόρτωσης
        loadingSpinner.style.display = 'none';
    }
}

// Εκκίνηση της διαδικασίας με τη φόρτωση της σελίδας
document.addEventListener('DOMContentLoaded', loadRecommendations);