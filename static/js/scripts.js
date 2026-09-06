document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('theme-toggle');
    const body = document.body;

    // saved mode in local storage
    const savedMode = localStorage.getItem('mode');
    if (savedMode) {
        body.classList.remove('light-mode', 'dark-mode');
        body.classList.add(savedMode);
        toggleButton.src = savedMode === 'dark-mode' ? "https://img.icons8.com/fluency/48/moon-symbol.png" : "https://img.icons8.com/fluency/48/moon-symbol.png";
    }

    toggleButton.addEventListener('click', function() {
        if (body.classList.contains('light-mode')) {
            body.classList.remove('light-mode');
            body.classList.add('dark-mode');
            localStorage.setItem('mode', 'dark-mode');
            toggleButton.src = "https://img.icons8.com/fluency/48/moon-symbol.png";  
        } else {
            body.classList.remove('dark-mode');
            body.classList.add('light-mode');
            localStorage.setItem('mode', 'light-mode');
            toggleButton.src = "https://img.icons8.com/fluency/48/moon-symbol.png";  
        }

        
    });
    const uploadForm = document.getElementById('upload-form');
    const loader = document.getElementById('loader');
    const results = document.getElementById('results');

    uploadForm.addEventListener('submit', function() {
        loader.style.display = 'block';
        results.textContent = '';
    });

    const analyzeButton = document.getElementById('analyze-button');
    analyzeButton.addEventListener('click', function() {
        loader.style.display = 'block';
        results.textContent = '';
        setTimeout(() => { loader.style.display = 'none'; }, 15000); //timeout for loader
    });



});
