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
    const allSkills = Array.from(new Set(courses.flatMap(c => [...(c.new_skills || []), ...(c.compatible_skills || [])])));
    const labels = courses.map(c => c.course_name || 'Unknown Course');

    const datasets = allSkills.map(skill => ({
        label: skill,
        data: courses.map(course => 1),
        backgroundColor: courses.map(course => {
            if ((course.new_skills || []).includes(skill)) return 'rgba(25, 135, 84, 0.8)';
            if ((course.compatible_skills || []).includes(skill)) return 'rgba(13, 202, 240, 0.8)';
            return 'rgba(220,220,220,0.3)';
        }),
        borderWidth: 0,
        barThickness: 12
    }));

    const ctx = document.getElementById('skillsHeatmapChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const color = context.dataset.backgroundColor[context.dataIndex];
                            if (color.includes('25, 135, 84')) return context.dataset.label + ': New Skill';
                            if (color.includes('13, 202, 240')) return context.dataset.label + ': Compatible Skill';
                            return context.dataset.label + ': -';
                        }
                    }
                }
            },
            scales: {
                x: { stacked: true, display: false },
                y: { stacked: true }
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

async function loadDegreePrograms(univId) {
    const dropdown = document.getElementById('degree-dropdown');
    dropdown.innerHTML = '<option value="">Select Degree Program</option>';
    try {
        const response = await fetch(`${API_BASE_URL}/universities/${univId}/degrees`);
        if (!response.ok) throw new Error('Failed to fetch degrees');
        const degrees = await response.json();
        degrees.forEach(degree => {
            const option = document.createElement('option');
            option.value = encodeURIComponent(degree.degree_titles?.[0] || degree.degree_type);
            option.textContent = `${degree.degree_type}: ${degree.degree_titles?.join(', ') || ''}`;
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading degrees:", error);
        const option = document.createElement('option');
        option.textContent = "Failed to load degrees";
        dropdown.appendChild(option);
    }
}

document.getElementById('degree-dropdown').addEventListener('change', (event) => {
    const degreeName = event.target.value;
    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    if (degreeName && univId) {
        fetchAndDisplayRecommendations(univId, degreeName);
    }
});

async function fetchAndDisplayRecommendations(univId, degreeName) {
    const headerElement = document.getElementById('courses-header');
    const loadingSpinner = document.getElementById('loading-spinner');
    const listElement = document.getElementById('course-recommendation-list');

    headerElement.textContent = `Loading courses...`;
    loadingSpinner.style.display = 'block';

    const endpoint = `${API_BASE_URL}/recommend/courses/${univId}/${degreeName}`;
    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        const recommendations = data.recommendations || [];
        displayCourseRecommendations(recommendations, degreeName);
    } catch (error) {
        console.error("Error loading courses:", error);
        loadingSpinner.style.display = 'none';
        listElement.innerHTML = `<li class="course-card" style="border-left-color: #dc3545;">Failed to load data: ${error.message}</li>`;
    }
}

async function initPage() {
    const params = new URLSearchParams(window.location.search);
    const univId = params.get('univ_id');
    if (!univId) return;

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
    document.getElementById('courses-header').textContent = `University: ${univName}`;

    await loadDegreePrograms(univId);
}

initPage();