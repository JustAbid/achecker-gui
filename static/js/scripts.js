document.addEventListener('DOMContentLoaded', function () {
    setupThemeToggle();
    setupUploadForm();
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

function setupUploadForm() {
    var form = document.getElementById('upload-form');
    if (!form) {
        return;
    }

    var fileInput = document.getElementById('file-input');
    var fileName = document.getElementById('file-name');
    var loader = document.getElementById('loader');
    var results = document.getElementById('results');

    if (fileInput && fileName) {
        fileInput.addEventListener('change', function () {
            fileName.textContent = fileInput.files.length ? fileInput.files[0].name : '';
        });
    }

    form.addEventListener('submit', function (event) {
        // No file: let the normal form POST through so the server renders the error.
        if (!fileInput || !fileInput.files.length) {
            return;
        }

        event.preventDefault();
        loader.hidden = false;
        results.innerHTML = '';

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: { 'X-Requested-With': 'fetch' }
        })
            .then(function (response) {
                return response.text();
            })
            .then(function (html) {
                results.innerHTML = html;
            })
            .catch(function () {
                results.innerHTML = '<p class="results-error">Request failed. Is the server running?</p>';
            })
            .then(function () {
                loader.hidden = true;
            });
    });
}
