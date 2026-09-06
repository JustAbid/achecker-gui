document.addEventListener('DOMContentLoaded', function () {
    setupThemeToggle();
    setupAnalysisForms();
});

function setupThemeToggle() {
    var toggle = document.getElementById('theme-toggle');
    if (!toggle) {
        return;
    }

    var root = document.documentElement;
    var moon = toggle.querySelector('.icon-moon');
    var sun = toggle.querySelector('.icon-sun');

    function apply(mode) {
        root.className = mode;
        var dark = mode === 'dark-mode';
        if (moon) { moon.hidden = dark; }
        if (sun) { sun.hidden = !dark; }
    }

    apply(root.className === 'dark-mode' ? 'dark-mode' : 'light-mode');

    toggle.addEventListener('click', function () {
        var next = root.className === 'dark-mode' ? 'light-mode' : 'dark-mode';
        apply(next);
        try {
            localStorage.setItem('mode', next);
        } catch (e) {}
    });
}

function setupAnalysisForms() {
    var loader = document.getElementById('loader');
    var results = document.getElementById('results');
    if (!results) {
        return;
    }

    function submitViaFetch(form) {
        if (loader) { loader.hidden = false; }
        results.innerHTML = '';

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: { 'X-Requested-With': 'fetch' }
        })
            .then(function (response) { return response.text(); })
            .then(function (html) { results.innerHTML = html; })
            .catch(function () {
                results.innerHTML = '<p class="results-error">Request failed. Is the server running?</p>';
            })
            .then(function () { if (loader) { loader.hidden = true; } });
    }

    var uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        var fileInput = document.getElementById('file-input');
        var fileName = document.getElementById('file-name');

        if (fileInput && fileName) {
            fileInput.addEventListener('change', function () {
                fileName.textContent = fileInput.files.length ? fileInput.files[0].name : '';
            });

            // On some Linux setups a fast double-click in the file dialog sends a
            // stray click back to the page as it closes, which reopens the picker
            // and drops the selection. Ignore clicks right after the window
            // regains focus (i.e. just after the dialog closed).
            var refocusedAt = 0;
            window.addEventListener('focus', function () { refocusedAt = Date.now(); });
            fileInput.addEventListener('click', function (event) {
                if (Date.now() - refocusedAt < 500) { event.preventDefault(); }
            });
        }

        uploadForm.addEventListener('submit', function (event) {
            // No file: let the normal POST through so the server renders the error.
            if (!fileInput || !fileInput.files.length) { return; }
            event.preventDefault();
            submitViaFetch(uploadForm);
        });
    }

    var sampleForms = document.querySelectorAll('.sample-form');
    for (var i = 0; i < sampleForms.length; i++) {
        sampleForms[i].addEventListener('submit', function (event) {
            event.preventDefault();
            submitViaFetch(event.currentTarget);
        });
    }
}
