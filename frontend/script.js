// === ΔΥΝΑΜΙΚΟ API PATH (Διορθωμένο για Docker Compose) ===
console.log("✅ script.js φορτώθηκε σωστά");

// Καθώς ο κώδικας εκτελείται στον browser (host) και το API εκτίθεται μέσω
// port mapping (8000:8000), χρησιμοποιούμε ΠΑΝΤΑ localhost:8000.
// Το 'http://api:8000' είναι σωστό μόνο εντός του Docker δικτύου.
const API_BASE_PATH = "http://localhost:8000";

/**
 * Ενημέρωση μετρικών (προγραμμάτων & δεξιοτήτων)
 */
function updateMetrics(metrics) {
    console.log("📊 Ενημέρωση μετρήσεων:", metrics);
    document.getElementById("total-programs").textContent =
        metrics.total_programs ?? "0";
    document.getElementById("recognized-skills").textContent =
        metrics.recognized_skills ?? "0";
}

/**
 * Πλοήγηση στη σελίδα αποτελεσμάτων ή μαθημάτων
 */
function navigate(type) {
    const selectElement = document.getElementById("university-select");
    const selectedUnivId = selectElement.value;

    console.log("➡️ navigate()", { type, selectedUnivId });

    if (!selectedUnivId || selectedUnivId === "Επιλέξτε Πανεπιστήμιο...") {
        alert("Παρακαλώ επιλέξτε Πανεπιστήμιο πρώτα.");
        return;
    }

    // Χρησιμοποιούμε το courses.html για μαθήματα, results.html για πτυχία
    const targetPage = type === 'courses' ? 'courses.html' : 'results.html';
    const url = `${targetPage}?type=${type}&univ_id=${selectedUnivId}`;

    console.log("🌐 Μετάβαση σε:", url);
    window.location.href = url;
}

/**
 * Φόρτωση πανεπιστημίων και σύνδεση κουμπιών
 */
async function loadUniversities() {
    console.log("🚀 Εκκίνηση loadUniversities()");
    const selectElement = document.getElementById("university-select");
    const degreesBtn = document.getElementById("degrees-btn");
    const coursesBtn = document.getElementById("courses-btn");

    console.log("🎓 Έλεγχος DOM Elements:", {
        selectElement,
        degreesBtn,
        coursesBtn,
    });

    // Έλεγχος αν όλα τα στοιχεία του DOM φορτώθηκαν
    if (!selectElement || !degreesBtn || !coursesBtn) {
        console.error("❌ Δεν βρέθηκαν κάποια στοιχεία στο DOM!");
        return;
    }

    // Κατάσταση φόρτωσης
    selectElement.disabled = true;
    selectElement.innerHTML =
        '<option value="" disabled selected>Φόρτωση Πανεπιστημίων...</option>';

    try {
        // 📡 Προσπάθεια κλήσης στο διορθωμένο API_BASE_PATH
        const response = await fetch(`${API_BASE_PATH}/universities`);
        console.log("📡 Απάντηση από /universities:", response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
        }

        const universities = await response.json();
        console.log("🎓 Πανεπιστήμια:", universities);

        selectElement.innerHTML = "";
        selectElement.appendChild(
            new Option("Επιλέξτε Πανεπιστήμιο...", "", true, true)
        );

        universities.forEach((univ) => {
            const option = document.createElement("option");
            option.value = univ.university_id; // Αυτό πρέπει να είναι το ID που χρειάζεται το API
            option.textContent = `${univ.university_name} (${univ.country})`;
            selectElement.appendChild(option);
        });

        selectElement.disabled = false;
    } catch (error) {
        console.error("❌ Σφάλμα φόρτωσης Πανεπιστημίων:", error);
        selectElement.innerHTML =
            '<option value="" disabled selected>Αποτυχία φόρτωσης δεδομένων. Ελέγξτε το API και το CORS.</option>';
    }

    // Κουμπιά αρχικά απενεργοποιημένα
    degreesBtn.disabled = true;
    coursesBtn.disabled = true;
    updateMetrics({ total_programs: 0, recognized_skills: 0 });

    // Όταν αλλάζει πανεπιστήμιο
    selectElement.addEventListener("change", async (event) => {
        const selectedUnivId = event.target.value;
        console.log("🏫 Επιλέχθηκε πανεπιστήμιο:", selectedUnivId);

        degreesBtn.disabled = !selectedUnivId;
        coursesBtn.disabled = !selectedUnivId;

        if (selectedUnivId) {
            try {
                const metricsResponse = await fetch(
                    `${API_BASE_PATH}/metrics/${selectedUnivId}`
                );
                if (!metricsResponse.ok) {
                    throw new Error(
                        `Metrics HTTP error! status: ${metricsResponse.status}`
                    );
                }
                const metrics = await metricsResponse.json();
                updateMetrics(metrics);
            } catch (error) {
                console.error("❌ Σφάλμα φόρτωσης μετρήσεων:", error);
                updateMetrics({
                    total_programs: "Error",
                    recognized_skills: "Error",
                });
            }
        } else {
            updateMetrics({ total_programs: 0, recognized_skills: 0 });
        }
    });

    // 🔔 Σύνδεση κουμπιών (με χρήση της navigate)
    degreesBtn.addEventListener("click", () => {
        console.log("🟦 Πάτησες ΠΡΟΤΕΙΝΕ ΠΤΥΧΙΑ");
        navigate("degrees");
    });

    coursesBtn.addEventListener("click", () => {
        console.log("🟩 Πάτησες ΠΡΟΤΕΙΝΕ ΜΑΘΗΜΑΤΑ");
        navigate("courses");
    });
}

// 🔹 Εκκίνηση όταν φορτωθεί πλήρως η σελίδα
document.addEventListener("DOMContentLoaded", loadUniversities);