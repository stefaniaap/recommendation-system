const API_BASE = "http://127.0.0.1:8000";
let currentMode = 'personal';

// --- Λειτουργία Μετάβασης (Hub <-> Form) ---

function setupNavigation() {
    const hub = document.getElementById('selectionHub');
    const formContainer = document.getElementById('mainFormContainer');
    const backBtn = document.getElementById('backToHubBtn');

    // Κουμπιά στο Hub
    document.getElementById('btnElectives').addEventListener('click', () => showForm('personal'));
    document.getElementById('btnNewDegrees').addEventListener('click', () => showForm('general'));

    // Κουμπί Επιστροφής στη Φόρμα
    backBtn.addEventListener('click', showHub);

    function showHub() {
        hub.style.display = 'flex'; // Εμφάνιση Hub
        formContainer.style.display = 'none'; // Απόκρυψη Φόρμας
    }

    function showForm(mode) {
        currentMode = mode;
        hub.style.display = 'none'; // Απόκρυψη Hub
        formContainer.style.display = 'block'; // Εμφάνιση Φόρμας

        // Καθορισμός τίτλου φόρμας και εμφάνιση σωστών φίλτρων
        const titleEl = document.getElementById('modeTitle');
        const actionBtn = document.getElementById('actionBtn');
        const personalFilters = document.getElementById('personalFilters');
        const generalFilters = document.getElementById('generalFilters');

        if (mode === 'personal') {
            titleEl.textContent = ' (Μαθήματα Επιλογής)';
            actionBtn.innerHTML = '<i class="fas fa-magic"></i> Πρότεινε Μαθήματα Επιλογής';
            personalFilters.style.display = 'grid';
            generalFilters.style.display = 'none';
        } else {
            titleEl.textContent = ' (Νέα Πτυχία & Μαθήματα)';
            actionBtn.innerHTML = '<i class="fas fa-search"></i> Εξερεύνηση Πτυχίων & Μαθημάτων';
            personalFilters.style.display = 'none';
            generalFilters.style.display = 'grid';
        }
    }
}

// --- Λογική Φόρτωσης Φίλτρων & Δεξιοτήτων ---

async function loadFilters() {
    const personalFiltersDiv = document.getElementById('personalFilters');
    const generalFiltersDiv = document.getElementById('generalFilters');

    // Δημιουργία HTML δομής για τα φίλτρα
    personalFiltersDiv.innerHTML = `
        <div class="filter-group">
            <label for="university"><i class="fas fa-school"></i> Πανεπιστήμιο:</label>
            <select id="university"><option value="">-- Επιλέξτε --</option></select>
        </div>
        <div class="filter-group">
            <label for="program"><i class="fas fa-book-reader"></i> Πρόγραμμα Σπουδών:</label>
            <select id="program"><option value="">-- Επιλέξτε --</option></select>
        </div>
    `;

    generalFiltersDiv.innerHTML = `
        <div class="filter-group">
            <label for="degreeType"><i class="fas fa-graduation-cap"></i> Τύπος Πτυχίου:</label>
            <select id="degreeType"><option value="">-- Όλοι --</option></select>
        </div>
        <div class="filter-group">
            <label for="country"><i class="fas fa-flag"></i> Χώρα:</label>
            <select id="country"><option value="">-- Όλες --</option></select>
        </div>
        <div class="filter-group">
            <label for="language"><i class="fas fa-language"></i> Γλώσσα:</label>
            <select id="language"><option value="">-- Όλες --</option></select>
        </div>
    `;

    try {
        const [degreeTypes, countries, languages, universities] = await Promise.all([
            fetch(`${API_BASE}/filters/degree-types`).then(r => r.json()),
            fetch(`${API_BASE}/filters/countries`).then(r => r.json()),
            fetch(`${API_BASE}/filters/languages`).then(r => r.json()),
            fetch(`${API_BASE}/filters/universities`).then(r => r.json())
        ]);

        // Εισαγωγή Γενικών Φίλτρων
        document.getElementById('degreeType').innerHTML += degreeTypes.map(item => `<option value="${item}">${item}</option>`).join('');
        document.getElementById('country').innerHTML += countries.map(item => `<option value="${item}">${item}</option>`).join('');
        document.getElementById('language').innerHTML += languages.map(item => `<option value="${item}">${item}</option>`).join('');

        // Εισαγωγή Πανεπιστημίων
        const universitySelect = document.getElementById("university");
        universitySelect.innerHTML += universities.map(u => `<option value="${u.id}">${u.name}</option>`).join('');

        // Δυναμική φόρτωση Προγραμμάτων ανά Πανεπιστήμιο
        universitySelect.addEventListener('change', async () => {
            const uniId = universitySelect.value;
            const programSelect = document.getElementById("program");
            programSelect.innerHTML = '<option value="">-- Επιλέξτε --</option>';
            if (uniId) {
                const programs = await fetch(`${API_BASE}/filters/university/${uniId}/programs`).then(r => r.json());
                programSelect.innerHTML += programs.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
            }
        });

    } catch (e) {
        console.error("Σφάλμα φόρτωσης φίλτρων. Βεβαιωθείτε ότι το backend τρέχει:", e);
    }
}

// Βοηθητική συνάρτηση για Accordion toggle
function setupAccordion(headerElement) {
    headerElement.addEventListener('click', () => {
        const content = headerElement.nextElementSibling;
        const icon = headerElement.querySelector('.accordion-icon');

        const isHidden = content.style.display === "none" || content.style.display === "";
        content.style.display = isHidden ? "block" : "none";
        icon.classList.toggle('fa-chevron-down', isHidden);
        icon.classList.toggle('fa-chevron-up', !isHidden);
    });
}

// Φόρτωση δεξιοτήτων (Accordion style)
async function loadSkills() {
    const skillsContainer = document.getElementById("skillsContainer");
    try {
        const groupedSkillsResponse = await fetch(`${API_BASE}/skills/grouped`).then(r => r.json());

        groupedSkillsResponse.forEach(groupItem => {
            const category = groupItem.group;
            const skills = groupItem.skills;

            const catDiv = document.createElement("div");
            catDiv.className = "skill-category";

            const header = document.createElement("div");
            header.className = "category-header";
            header.innerHTML = `${category} <i class="fas fa-chevron-down accordion-icon"></i>`;
            setupAccordion(header);
            catDiv.appendChild(header);

            const content = document.createElement("div");
            content.className = "category-content";
            content.style.display = 'none';

            skills.forEach(skill => {
                const label = document.createElement("label");
                label.className = "skill-item";
                const cb = document.createElement("input");
                cb.type = "checkbox";
                cb.value = skill.id;
                label.appendChild(cb);
                label.appendChild(document.createTextNode(" " + skill.name));
                content.appendChild(label);
            });

            catDiv.appendChild(content);
            skillsContainer.appendChild(catDiv);
        });
    } catch (e) {
        skillsContainer.innerHTML = `<p style="color:red;">Δεν φορτώθηκαν οι δεξιότητες. Σφάλμα στο backend.</p>`;
    }
}

// --- CORE LOGIC (Αναζήτηση) ---

async function performAction() {
    const skillIds = Array.from(document.querySelectorAll("#skillsContainer input[type=checkbox]:checked"))
        .map(cb => parseInt(cb.value));

    let url = '';

    if (skillIds.length === 0) {
        displayError("Παρακαλώ επιλέξτε τουλάχιστον μία δεξιότητα (Skill).");
        return;
    }

    try {
        if (currentMode === 'personal') {
            const universityId = document.getElementById("university").value;
            const programId = document.getElementById("program").value;

            if (!universityId || !programId) {
                displayError("Για Προσωπική Σύσταση, πρέπει να επιλέξετε Πανεπιστήμιο και Πρόγραμμα Σπουδών.");
                return;
            }
            url = `${API_BASE}/recommend/elective-courses?program_id=${programId}&target_skills=${skillIds.join(',')}`;

        } else { // general mode
            const degreeType = document.getElementById("degreeType").value;
            const country = document.getElementById("country").value;
            const language = document.getElementById("language").value;

            const params = new URLSearchParams();
            skillIds.forEach(id => params.append('skill_ids', id));
            if (degreeType) params.append('degree_type', degreeType);
            if (country) params.append('country', country);
            if (language) params.append('language', language);

            url = `${API_BASE}/recommend/general-search?${params.toString()}`;
        }

        const res = await fetch(url);

        if (!res.ok) {
            const errorText = await res.text();
            displayError(`Σφάλμα: ${res.status}. ${errorText}`);
            return;
        }

        const data = await res.json();
        displayResults(data, currentMode);

    } catch (error) {
        displayError(`Προέκυψε σφάλμα κατά την επικοινωνία με τον server. Βεβαιωθείτε ότι το Backend τρέχει σωστά: ${error.message}`);
    }
}

// Εμφάνιση Σφάλματος
function displayError(message) {
    document.getElementById("results").innerHTML = `<p style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; max-width: 1000px; margin: 20px auto;">${message}</p>`;
}

// Εμφάνιση αποτελεσμάτων (Με Progress Bars)
function displayResults(data, mode) {
    const container = document.getElementById("results");
    container.innerHTML = "";

    const hasPrograms = data.degree_programs && data.degree_programs.length;
    const hasCourses = data.courses && data.courses.length;

    if (!hasPrograms && !hasCourses) {
        container.innerHTML = `<p style="padding: 20px; text-align: center; color: var(--secondary-color);">Δεν βρέθηκαν αποτελέσματα με τα επιλεγμένα κριτήρια.</p>`;
        return;
    }

    // 1. Προγράμματα Σπουδών (Μόνο στη Γενική Αναζήτηση)
    if (mode === 'general' && hasPrograms) {
        const progHeader = document.createElement('h2');
        progHeader.innerHTML = '<i class="fas fa-graduation-cap"></i> Προτεινόμενα Πτυχία';
        container.appendChild(progHeader);

        const grid = document.createElement('div');
        grid.className = 'results-grid';
        container.appendChild(grid);

        data.degree_programs.forEach(p => {
            const score = p.match_score !== null ? (p.match_score * 100).toFixed(0) : 0;
            const programTitle = p.degree_titles ? (p.degree_titles.en || p.degree_titles[Object.keys(p.degree_titles)[0]]) : 'Άγνωστο Πρόγραμμα';

            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <p class="card-meta"><i class="fas fa-certificate"></i> ${p.degree_type} | ${p.language || 'N/A'}</p>
                <h3 class="card-title">${programTitle}</h3>
                <p class="card-meta"><i class="fas fa-university"></i> ${p.university.university_name}, ${p.university.country}</p>
                
                <div class="score-container">
                    <small>Συνάφεια Δεξιοτήτων: <strong>${score}%</strong></small>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${score}%;"></div>
                    </div>
                </div>
                ${p.matched_skills.map(s => `<span class="skill-tag">${s}</span>`).join('')}
            `;
            grid.appendChild(card);
        });
    }

    // 2. Μαθήματα (Και στις δύο ροές)
    if (hasCourses) {
        const courseHeader = document.createElement('h2');
        const title = mode === 'personal' ? 'Προτεινόμενα Μαθήματα Επιλογής' : 'Συναφή Μαθήματα';
        courseHeader.innerHTML = `<i class="fas fa-book"></i> ${title}`;
        container.appendChild(courseHeader);

        const grid = document.createElement('div');
        grid.className = 'results-grid';
        container.appendChild(grid);

        data.courses.forEach(c => {
            const score = c.match_score !== null ? (c.match_score * 100).toFixed(0) : 0;

            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <h3 class="card-title">${c.lesson_name}</h3>
                <p class="card-meta"><i class="fas fa-university"></i> ${c.university.university_name}, ${c.university.country}</p>
                
                <div class="score-container">
                    <small>Συνάφεια Δεξιοτήτων: <strong>${score}%</strong></small>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${score}%;"></div>
                    </div>
                </div>
                ${c.matched_skills.map(s => `<span class="skill-tag">${s}</span>`).join('')}
            `;
            grid.appendChild(card);
        });
    }
}

// Event listeners
document.getElementById("actionBtn").addEventListener("click", performAction);

// Αρχική φόρτωση
loadFilters();
loadSkills();
setupNavigation();