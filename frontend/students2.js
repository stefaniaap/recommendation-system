// university_script.js

// Base URL for the backend API (FastAPI)
const API_BASE_URL = 'http://api:8000';

// -----------------------------------------------
// Function: updateMetrics
// Updates the metrics section in the UI
// -----------------------------------------------
function updateMetrics(metrics) {
    document.getElementById("total-programs").textContent =
        metrics.total_programs ?? "0";
    document.getElementById("recognized-skills").textContent =
        metrics.recognized_skills ?? "0";
}

// -----------------------------------------------
// Function: loadUniversities
// Fetches the list of universities from the API
// and initializes the dropdown and buttons
// -----------------------------------------------
async function loadUniversities() {
    const selectElement = document.getElementById("university-select");
    const degreesBtn = document.getElementById("degrees-btn");
    const coursesBtn = document.getElementById("courses-btn");

    // Disable dropdown while loading
    selectElement.disabled = true;
    selectElement.innerHTML =
        '<option value="" disabled selected>Loading Universities...</option>';

    try {
        // Call the backend to get all universities
        const response = await fetch(`${API_BASE_URL}/universities`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const universities = await response.json();

        // Clear existing options
        selectElement.innerHTML = "";
        selectElement.appendChild(
            new Option("Select University...", "", true, true)
        );

        // Add each university to the dropdown
        universities.forEach((univ) => {
            const option = document.createElement("option");
            option.value = univ.university_id;
            option.textContent = `${univ.university_name} (${univ.country})`;
            selectElement.appendChild(option);
        });

        selectElement.disabled = false;
    } catch (error) {
        console.error("❌ Error loading universities:", error);
        selectElement.innerHTML =
            '<option value="" disabled selected>Failed to load universities. Check API connection.</option>';
    }

    // Disable buttons until a university is selected
    degreesBtn.disabled = true;
    coursesBtn.disabled = true;

    // Reset metrics display
    updateMetrics({ total_programs: 0, recognized_skills: 0 });

    // -----------------------------------------------
    // When a university is selected from the dropdown
    // -----------------------------------------------
    selectElement.addEventListener("change", async (event) => {
        const selectedUnivId = event.target.value;

        // Enable buttons only if a university is selected
        degreesBtn.disabled = !selectedUnivId;
        coursesBtn.disabled = !selectedUnivId;

        if (selectedUnivId) {
            try {
                // Fetch metrics for the selected university
                const metricsResponse = await fetch(
                    `${API_BASE_URL}/metrics/${selectedUnivId}`
                );
                if (!metricsResponse.ok) {
                    throw new Error(
                        `Metrics HTTP error! status: ${metricsResponse.status}`
                    );
                }
                const metrics = await metricsResponse.json();
                updateMetrics(metrics);
            } catch (error) {
                console.error("❌ Error loading metrics:", error);
                updateMetrics({
                    total_programs: "Error",
                    recognized_skills: "Error",
                });
            }
        } else {
            // Reset metrics if no university selected
            updateMetrics({ total_programs: 0, recognized_skills: 0 });
        }
    });

    // -----------------------------------------------
    // Navigation buttons for results and courses pages
    // -----------------------------------------------
    degreesBtn.addEventListener("click", () => navigate("degrees"));
    coursesBtn.addEventListener("click", () => navigate("courses"));
}

// -----------------------------------------------
// Function: navigate
// Redirects to the corresponding analysis page
// -----------------------------------------------
function navigate(type) {
    const selectElement = document.getElementById("university-select");
    const selectedUnivId = selectElement.value;

    if (!selectedUnivId) {
        alert("Please select a university first.");
        return;
    }

    // Choose which page to navigate to
    const targetPage = type === "courses" ? "courses.html" : "results.html";
    window.location.href = `${targetPage}?type=${type}&univ_id=${selectedUnivId}`;
}

// -----------------------------------------------
// Initialize the script when the DOM is fully loaded
// -----------------------------------------------
document.addEventListener("DOMContentLoaded", loadUniversities);
