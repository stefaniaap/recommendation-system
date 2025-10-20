// script.js

const API_BASE_URL = 'http://127.0.0.1:8000';

function updateMetrics(metrics) {
    document.getElementById('total-programs').textContent = metrics.total_programs ?? '0';
    document.getElementById('recognized-skills').textContent = metrics.recognized_skills ?? '0';
}

/**
 * Φορτώνει τη λίστα Πανεπιστημίων από το API.
 */
async function loadUniversities() {
    const selectElement = document.getElementById('university-select');
    const degreesBtn = document.getElementById('degrees-btn');
    const coursesBtn = document.getElementById('courses-btn');

    selectElement.disabled = true;
    selectElement.innerHTML = '<option value="" disabled selected>Φόρτωση Πανεπιστημίων...</option>';

    try {
        const response = await fetch(`${API_BASE_URL}/universities`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const universities = await response.json();

        selectElement.innerHTML = '';
        selectElement.appendChild(
            new Option("Επιλέξτε Πανεπιστήμιο...", "", true, true)
        );

        universities.forEach(univ => {
            const option = document.createElement('option');
            option.value = univ.university_id;
            option.textContent = `${univ.university_name} (${univ.country})`;
            selectElement.appendChild(option);
        });

        selectElement.disabled = false;

    } catch (error) {
        console.error("Σφάλμα φόρτωσης Πανεπιστημίων:", error);
        selectElement.innerHTML = '<option value="" disabled selected>Αποτυχία φόρτωσης δεδομένων.</option>';
    }

    degreesBtn.disabled = true;
    coursesBtn.disabled = true;
    updateMetrics({ total_programs: 0, recognized_skills: 0 });


    selectElement.addEventListener('change', async (event) => {
        const selectedUnivId = event.target.value;

        degreesBtn.disabled = !selectedUnivId;
        coursesBtn.disabled = !selectedUnivId;

        if (selectedUnivId) {
            try {
                const metricsResponse = await fetch(`${API_BASE_URL}/metrics/${selectedUnivId}`);
                if (!metricsResponse.ok) {
                    throw new Error(`Metrics HTTP error! status: ${metricsResponse.status}`);
                }
                const metrics = await metricsResponse.json();
                updateMetrics(metrics);

            } catch (error) {
                console.error("Σφάλμα φόρτωσης μετρήσεων:", error);
                updateMetrics({ total_programs: 'Error', recognized_skills: 'Error' });
            }
        } else {
            updateMetrics({ total_programs: 0, recognized_skills: 0 });
        }
    });
}

/**
 * Διαχειρίζεται την πλοήγηση στη νέα σελίδα, περνώντας το univ_id.
 * @param {string} type - 'degrees' ή 'courses'.
 */
function navigate(type) {
    const selectElement = document.getElementById('university-select');
    const selectedUnivId = selectElement.value;

    if (!selectedUnivId) {
        alert("Παρακαλώ επιλέξτε Πανεπιστήμιο πρώτα.");
        return;
    }

    // 🚨 ΑΝΑΔΙΕΥΘΥΝΣΗ στο results.html με Query Parameters
    window.location.href = `results.html?type=${type}&univ_id=${selectedUnivId}`;
}

// Εκκίνηση της διαδικασίας φόρτωσης μόλις φορτωθεί το DOM
document.addEventListener('DOMContentLoaded', loadUniversities);