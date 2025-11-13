
const API_BASE_URL = 'http://localhost:8000';


function scoreToCourseColor(score) {
    const clampedScore = Math.max(0, Math.min(1, score));
    const lowR = 198, lowG = 226, lowB = 189;
    const highR = 40, highG = 167, highB = 69;
    const r = Math.round(lowR + (highR - lowR) * clampedScore);
    const g = Math.round(lowG + (highG - lowG) * clampedScore);
    const b = Math.round(lowB + (highB - lowB) * clampedScore);
    return `rgb(${r}, ${g}, ${b})`;
}

function displayCourseHeatmap(courses) {
    const allSkills = Array.from(new Set(
        courses.flatMap(c => [...(c.new_skills || []), ...(c.compatible_skills || [])])
    ));

    const courseNames = courses.map(c => c.course_name);

    // Δημιουργία χρωμάτων για κάθε skill (hue-based)
    const skillHueMap = {};
    allSkills.forEach((skill, i) => skillHueMap[skill] = Math.round((i * 137.508) % 360));

    // Δημιουργία δεδομένων για heatmap
    const datasets = allSkills.map(skill => {
        const data = courseNames.map(courseName => {
            const course = courses.find(c => c.course_name === courseName);
            if (!course) return 0;
            if ((course.new_skills || []).includes(skill)) return 2; // new skill
            if ((course.compatible_skills || []).includes(skill)) return 1; // compatible
            return 0; // δεν υπάρχει
        });

        return {
            label: skill,
            data: data,
            backgroundColor: data.map(val => {
                if (val === 2) return `hsl(${skillHueMap[skill]}, 70%, 50%)`; // new
                if (val === 1) return `hsl(${skillHueMap[skill]}, 70%, 80%)`; // compatible
                return 'rgba(0,0,0,0)'; // κενό
            }),
            borderColor: '#fff',
            borderWidth: 1,
            barThickness: 20
        };
    });

    const ctx = document.getElementById('skillsHeatmapChart').getContext('2d');
    if (window.skillsHeatmapChart && typeof window.skillsHeatmapChart.destroy === 'function') {
        window.skillsHeatmapChart.destroy();
    }

    window.skillsHeatmapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: courseNames, // y-axis = courses
            datasets: datasets
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const course = ctx.label;
                            const skill = ctx.dataset.label;
                            const val = ctx.raw;
                            if (val === 2) return `${course}: ${skill} (New)`;
                            if (val === 1) return `${course}: ${skill} (Compatible)`;
                            return null;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        generateLabels: chart => {
                            return allSkills.map(skill => {
                                const hue = skillHueMap[skill];
                                return [
                                    { text: `${skill} (New)`, fillStyle: `hsl(${hue},70%,50%)` },
                                    { text: `${skill} (Compatible)`, fillStyle: `hsl(${hue},70%,80%)` }
                                ];
                            }).flat();
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: false,
                    title: { display: true, text: 'Skills' }
                },
                y: {
                    stacked: false,
                    title: { display: true, text: 'Courses' }
                }
            }
        }
    });
}



function displayCourseRecommendations(courses, degreeName) {
    const resultsContainer = document.getElementById('course-recommendation-list');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (loadingSpinner) loadingSpinner.style.display = 'none';
    titleElement.textContent = `📚 Recommended Courses for: ${decodeURIComponent(degreeName)}`;

    if (!courses || courses.length === 0) {
        resultsContainer.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">❌ No recommended courses found.</li>`;
        return;
    }

    let htmlContent = '';
    courses.forEach(course => {
        const score = course.score ? course.score.toFixed(3) : 'N/A';
        const color = scoreToCourseColor(course.score || 0);
        const description = course.description || 'Not available.';
        const objectives = course.objectives || 'Not available.';
        const learning_outcomes = course.learning_outcomes || 'Not available.';
        const course_content = course.course_content || 'Not available.';

        htmlContent += `
                    <li class="course-card" style="border-left-color: ${color};">
                        <div class="card-header">
                            <p class="course-name">${course.course_name || 'Unknown Course'}</p>
                            <div class="score-badge" style="background-color: ${color};">Score: ${score}</div>
                        </div>
                        <div class="info-grid mt-3">
                            <div class="info-item"><h6>🎯 Objectives</h6><p>${objectives.substring(0, 150)}...</p></div>
                            <div class="info-item"><h6>💡 Learning Outcomes</h6><p>${learning_outcomes.substring(0, 150)}...</p></div>
                        </div>
                        <div class="info-section mt-3 p-3" style="border: 1px dashed #ced4da; background-color: #f7f7f7;">
                            <h6>🌐 Description Summary</h6>
                            <p style="font-size: 0.85em;">${description.substring(0, 200)}...</p>
                            <details>
                                <summary style="cursor:pointer;color:#007bff;font-weight:500;margin-top:10px;">Full Details</summary>
                                <h6 class="mt-2">Full Description</h6><p style="font-size:0.8em;">${description}</p>
                                <h6 class="mt-2">Course Content</h6><p style="font-size:0.8em;">${course_content}</p>
                            </details>
                        </div>
                    </li>
                `;
    });

    resultsContainer.innerHTML = htmlContent;
    displayCourseHeatmap(courses);
}

async function fetchAndDisplayRecommendations() {
    const headerElement = document.getElementById('courses-header');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');
    const listElement = document.getElementById('course-recommendation-list');

    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    const degreeName = params.get('degree_name');

    if (!univId || !degreeName) {
        headerElement.textContent = `Error: URL data missing.`;
        titleElement.textContent = "";
        loadingSpinner.style.display = 'none';
        return;
    }

    const decodedDegreeName = decodeURIComponent(degreeName);
    let univName = `University ID: ${univId}`;

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

    headerElement.textContent = `University: ${univName}`;
    titleElement.textContent = `Loading Courses for ${decodedDegreeName}...`;
    loadingSpinner.style.display = 'block';

    const endpoint = `${API_BASE_URL}/recommend/new_degree/${encodeURIComponent(degreeName)}`;

    console.log("Calling API URL:", endpoint);

    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        const recommendations = data.recommendations || [];
        displayCourseRecommendations(recommendations, degreeName);
    } catch (error) {
        console.error("Error loading recommended courses:", error);
        loadingSpinner.style.display = 'none';
        listElement.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">Failed to load data: ${error.message}</li>`;
    }
}

fetchAndDisplayRecommendations();