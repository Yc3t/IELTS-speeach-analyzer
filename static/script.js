document.addEventListener('DOMContentLoaded', (event) => {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const analysisResult = document.getElementById('analysisResult');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const newAnalysisButton = document.getElementById('newAnalysis');
    const recentEntriesList = document.getElementById('recentEntriesList');

    function updateRecentEntriesList() {
        axios.get('/recent_entries')
            .then(response => {
                const entries = response.data;
                recentEntriesList.innerHTML = '';
                if (entries.length === 0) {
                    const li = document.createElement('li');
                    li.textContent = 'No recent entries';
                    recentEntriesList.appendChild(li);
                } else {
                    entries.forEach((entry) => {
                        const li = document.createElement('li');
                        
                        const icon = document.createElement('img');
                        icon.src = '/static/file.svg';
                        icon.alt = 'File';
                        icon.className = 'file-icon';
                        
                        const entryText = document.createElement('span');
                        entryText.textContent = entry.filename;
                        
                        const deleteButton = document.createElement('button');
                        deleteButton.className = 'delete-button';
                        deleteButton.textContent = 'X';
                        
                        li.appendChild(icon);
                        li.appendChild(entryText);
                        li.appendChild(deleteButton);
                        
                        li.addEventListener('click', (e) => {
                            if (e.target !== deleteButton) {
                                loadAnalysis(entry.analysis_html);
                            }
                        });
                        
                        deleteButton.addEventListener('click', (e) => {
                            e.stopPropagation();
                            deleteEntry(entry.filename);
                        });
                        
                        recentEntriesList.appendChild(li);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching recent entries:', error);
                recentEntriesList.innerHTML = '<li>Error loading recent entries</li>';
            });
    }

    function loadAnalysis(analysisFile) {
        axios.get(`/analysis/${analysisFile}`)
            .then(response => {
                analysisResult.innerHTML = response.data;
                dropArea.style.display = 'none';
            })
            .catch(error => {
                console.error('Error loading analysis:', error);
                analysisResult.innerHTML = 'Error loading analysis.';
            });
    }

    function deleteEntry(filename) {
        if (confirm('Are you sure you want to delete this entry?')) {
            axios.delete(`/delete_entry/${filename}`)
                .then(response => {
                    if (response.data.success) {
                        updateRecentEntriesList();
                        resetMainContent();
                    } else {
                        alert('Error deleting entry: ' + response.data.message);
                    }
                })
                .catch(error => {
                    console.error('Error deleting entry:', error);
                    alert('Error deleting entry. Please try again.');
                });
        }
    }

    function resetMainContent() {
        analysisResult.innerHTML = '';
        dropArea.style.display = 'block';
    }

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropArea.classList.add('dragover');
    }

    function unhighlight(e) {
        dropArea.classList.remove('dragover');
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    uploadButton.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type === 'video/mp4' || file.type === 'audio/mpeg') {
                uploadFile(file);
            } else {
                alert('Please upload an MP4 video or MP3 audio file.');
            }
        }
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        loadingSpinner.style.display = 'block';
        analysisResult.innerHTML = '';
        dropArea.style.display = 'none';

        axios.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        .then(response => {
            loadingSpinner.style.display = 'none';
            analysisResult.innerHTML = response.data.analysis;
            updateRecentEntriesList();
        })
        .catch(error => {
            loadingSpinner.style.display = 'none';
            console.error('Error:', error);
            analysisResult.innerHTML = 'An error occurred during analysis.';
        });
    }

    newAnalysisButton.addEventListener('click', () => {
        resetMainContent();
    });

    updateRecentEntriesList();
});