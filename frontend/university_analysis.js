const API_BASE_URL = "http://localhost:8000";

function updateMetrics(metrics) {
    document.getElementById("total-programs").textContent =
        metrics.total_programs ?? "0";
    document.getElementById("recognized-skills").textContent =
        metrics.recognized_skills ?? "0";
}

async function loadUniversitiesCustom() {
    const wrapper = document.querySelector('.custom-select-wrapper');
    const trigger = wrapper.querySelector('.custom-select-trigger');
    const optionsContainer = wrapper.querySelector('.custom-options');

    // Fetch universities
    try {
        const response = await fetch(`${API_BASE_URL}/universities`);
        const universities = await response.json();

        optionsContainer.innerHTML = '';
        universities.forEach(univ => {
            const option = document.createElement('div');
            option.classList.add('custom-option');
            option.dataset.value = univ.university_id;
            option.textContent = `${univ.university_name} (${univ.country})`;
            optionsContainer.appendChild(option);
        });
    } catch (err) {
        optionsContainer.innerHTML = '<div class="custom-option">Failed to load universities</div>';
        console.error(err);
    }

    // Toggle dropdown
    trigger.addEventListener('click', () => {
        wrapper.querySelector('.custom-select').classList.toggle('open');
    });

    // Option selection
    optionsContainer.addEventListener('click', e => {
        if (e.target.classList.contains('custom-option')) {
            const selected = optionsContainer.querySelector('.selected');
            if (selected) selected.classList.remove('selected');
            e.target.classList.add('selected');
            trigger.textContent = e.target.textContent;
            wrapper.querySelector('.custom-select').classList.remove('open');

            // Enable buttons & update metrics
            const selectedUnivId = e.target.dataset.value;
            document.getElementById('degrees-btn').disabled = false;
            document.getElementById('courses-btn').disabled = false;

            // Fetch metrics
            fetch(`${API_BASE_URL}/metrics/${selectedUnivId}`)
                .then(res => res.json())
                .then(metrics => updateMetrics(metrics))
                .catch(err => {
                    console.error(err);
                    updateMetrics({ total_programs: 'Error', recognized_skills: 'Error' });
                });
        }
    });

    // Close dropdown if click outside
    document.addEventListener('click', e => {
        if (!wrapper.contains(e.target)) {
            wrapper.querySelector('.custom-select').classList.remove('open');
        }
    });
}

// Navigation buttons
document.getElementById('degrees-btn').addEventListener('click', () => {
    const selected = document.querySelector('.custom-option.selected');
    if (!selected) return alert('Please select a university first.');
    const univ_id = selected.dataset.value;
    window.location.href = `new_degree_purposals.html?type=degrees&univ_id=${univ_id}`;
});

document.getElementById('courses-btn').addEventListener('click', () => {
    const selected = document.querySelector('.custom-option.selected');
    if (!selected) return alert('Please select a university first.');
    const univ_id = selected.dataset.value;
    window.location.href = `curriculum_enhancement.html?type=courses&univ_id=${univ_id}`;
});

document.addEventListener('DOMContentLoaded', loadUniversitiesCustom);



