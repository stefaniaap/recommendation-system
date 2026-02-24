// =====================================================
// ALTERNATIVE VISUALIZATIONS - Much More Understandable!
// =====================================================
// Choose ONE of these three options to replace the heatmap
// =====================================================

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



// =====================================================
// OPTION 3: STACKED HORIZONTAL BAR (RECOMMENDED!)
// Shows all skills with indication of which courses cover them
// ΠΛΕΟΝΕΚΤΗΜΑΤΑ: Πιο κατανοητό από όλα, skills-focused
// =====================================================
// =====================================================
// ΣΩΣΤΗ ΟΠΤΙΚΟΠΟΙΗΣΗ: Top Recommended Courses
// Δείχνει ποια μαθήματα να προσθέσεις στο νέο πτυχίο
// =====================================================
function displayRecommendedCoursesChart(courses) {
    const ctx = document.getElementById("skillsHeatmapChart").getContext("2d");

    // Destroy existing chart
    if (window.skillsHeatmapChart && typeof window.skillsHeatmapChart.destroy === 'function') {
        window.skillsHeatmapChart.destroy();
    }

    // Πάρε τα top 10 μαθήματα
    const topCourses = courses.slice(0, 10);

    // Ετοίμασε τα data
    const labels = topCourses.map(c => c.course_name || 'Unknown Course');
    const scores = topCourses.map(c => c.score || 0);
    const colors = topCourses.map(c => scoreToCourseColor(c.score || 0));

    window.skillsHeatmapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Recommendation Score',
                data: scores,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('rgb', 'rgba').replace(')', ', 1)')),
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal bars
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Recommended Courses For The New Degree',
                    font: { size: 20, weight: 'bold' },
                    padding: { top: 10, bottom: 30 },
                    color: '#2c3e50'
                },
                legend: {
                    display: false // Δεν χρειάζεται legend
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    padding: 16,
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 12 },
                    callbacks: {
                        title: function (context) {
                            return context[0].label;
                        },
                        label: function (context) {
                            const course = topCourses[context.dataIndex];
                            const score = (course.score || 0).toFixed(3);
                            return `Score: ${score}`;
                        },
                        afterLabel: function (context) {
                            const course = topCourses[context.dataIndex];

                            let info = [];

                            // Emerging Skills
                            if (course.new_skills && course.new_skills.length > 0) {
                                const skillsPreview = course.new_skills.slice(0, 3).join(', ');
                                const more = course.new_skills.length > 3 ? ` (+${course.new_skills.length - 3} more)` : '';
                                info.push(`\n Emerging Skills:\n${skillsPreview}${more}`);
                            }

                            // Compatible Skills
                            if (course.compatible_skills && course.compatible_skills.length > 0) {
                                const skillsPreview = course.compatible_skills.slice(0, 3).join(', ');
                                const more = course.compatible_skills.length > 3 ? ` (+${course.compatible_skills.length - 3} more)` : '';
                                info.push(`\nCompatible Skills:\n${skillsPreview}${more}`);
                            }

                            return info.join('\n');
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 1,
                    title: {
                        display: true,
                        text: 'Recommendation Score (0-1)',
                        font: { size: 14, weight: 'bold' },
                        color: '#2c3e50'
                    },
                    ticks: {
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    ticks: {
                        font: { size: 11 },
                        color: '#2c3e50',
                        // Κόψε τα μεγάλα ονόματα μαθημάτων
                        callback: function (value, index) {
                            const label = this.getLabelForValue(value);
                            return label.length > 40 ? label.substring(0, 37) + '...' : label;
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// =====================================================
// Display course recommendations on the page
// =====================================================
function displayCourseRecommendations(courses, degreeName) {
    const resultsContainer = document.getElementById('course-recommendation-list');
    const titleElement = document.getElementById('courses-title');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (loadingSpinner) loadingSpinner.style.display = 'none';
    titleElement.textContent = ` Recommended Courses for: ${decodeURIComponent(degreeName)}`;

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

    displayRecommendedCoursesChart(courses);
}


// =====================================================
// Fetch recommendations from API and display
// =====================================================
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