// Configuration
const MAX_SIZE_MP3 = 50 * 1024 * 1024; // 50 MB
const MAX_SIZE_VIDEO = 100 * 1024 * 1024; // 100 MB
const SUPPORTED_TYPES = {
    'audio/mpeg': { ext: '.mp3', maxSize: MAX_SIZE_MP3 },
    'video/mp4': { ext: '.mp4', maxSize: MAX_SIZE_VIDEO },
    'video/mpeg': { ext: '.mpeg', maxSize: MAX_SIZE_VIDEO }
};

const API_BASE_URL = 'http://localhost:5000';

// State
let files = [];

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const filesList = document.getElementById('filesList');
const actions = document.getElementById('actions');
const compressBtn = document.getElementById('compressBtn');
const clearBtn = document.getElementById('clearBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const resultsSummary = document.getElementById('resultsSummary');
const downloadBtn = document.getElementById('downloadBtn');

// State for download
let downloadBlob = null;

// Event Listeners
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', handleDragOver);
dropZone.addEventListener('dragleave', handleDragLeave);
dropZone.addEventListener('drop', handleDrop);
fileInput.addEventListener('change', handleFileSelect);
compressBtn.addEventListener('click', handleCompress);
clearBtn.addEventListener('click', handleClear);

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
}

function handleFileSelect(e) {
    const selectedFiles = Array.from(e.target.files);
    addFiles(selectedFiles);
    e.target.value = ''; // Reset input
}

// File Management
function addFiles(newFiles) {
    newFiles.forEach(file => {
        const validation = validateFile(file);
        files.push({
            file: file,
            id: Date.now() + Math.random(),
            valid: validation.valid,
            error: validation.error
        });
    });

    renderFilesList();
    updateActions();
}

function validateFile(file) {
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    // Check if file type is supported
    const typeConfig = Object.values(SUPPORTED_TYPES).find(t => t.ext === ext);
    if (!typeConfig) {
        return {
            valid: false,
            error: `Unsupported file type: ${ext}`
        };
    }

    // Check file size
    if (file.size > typeConfig.maxSize) {
        const maxSizeMB = typeConfig.maxSize / (1024 * 1024);
        return {
            valid: false,
            error: `File exceeds ${maxSizeMB} MB limit`
        };
    }

    return { valid: true, error: null };
}

function removeFile(id) {
    files = files.filter(f => f.id !== id);
    renderFilesList();
    updateActions();
}

function handleClear() {
    files = [];
    renderFilesList();
    updateActions();
    hideResults();
}

// UI Rendering
function renderFilesList() {
    if (files.length === 0) {
        filesList.innerHTML = '';
        return;
    }

    filesList.innerHTML = files.map(fileData => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">${fileData.file.name}</div>
                <div class="file-details">
                    ${formatFileSize(fileData.file.size)} • ${getFileType(fileData.file.name)}
                    ${!fileData.valid ? `• ${fileData.error}` : ''}
                </div>
            </div>
            <div class="file-status ${fileData.valid ? 'valid' : 'invalid'}">
                ${fileData.valid ? '✓ Valid' : '✗ Invalid'}
            </div>
            <button class="file-remove" onclick="removeFile(${fileData.id})">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
            </button>
        </div>
    `).join('');
}

function updateActions() {
    if (files.length > 0) {
        actions.style.display = 'flex';
        const hasValidFiles = files.some(f => f.valid);
        compressBtn.disabled = !hasValidFiles;
    } else {
        actions.style.display = 'none';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function getFileType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    return ext.toUpperCase();
}

// Real Compression via Backend
async function handleCompress() {
    const validFiles = files.filter(f => f.valid);

    if (validFiles.length === 0) {
        alert('No valid files to compress!');
        return;
    }

    // Disable button
    compressBtn.disabled = true;
    compressBtn.textContent = 'Compressing...';

    // Hide actions, show progress
    actions.style.display = 'none';
    progressSection.style.display = 'block';
    hideResults();

    try {
        // Get settings values
        const settings = {
            targetSize: document.getElementById('targetSize').value,
            sizeUnit: document.getElementById('sizeUnit').value,
            sampleRate: document.getElementById('sampleRate').value,
            channels: document.getElementById('channels').value,
            bitrate: document.getElementById('bitrate').value
        };

        // Create FormData
        const formData = new FormData();
        validFiles.forEach(fileData => {
            formData.append('files', fileData.file);
        });

        // Append settings
        Object.keys(settings).forEach(key => {
            formData.append(key, settings[key]);
        });

        // Update progress
        progressFill.style.width = '50%';
        progressText.textContent = 'Uploading and compressing files...';

        // Send to backend
        const response = await fetch(`${API_BASE_URL}/api/compress`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Compression failed');
        }

        // Get the blob
        downloadBlob = await response.blob();

        // Complete progress
        progressFill.style.width = '100%';
        progressText.textContent = 'Compression complete!';

        // Show results
        setTimeout(() => {
            progressSection.style.display = 'none';
            showResults(validFiles, downloadBlob);
        }, 500);

    } catch (error) {
        alert(`Error: ${error.message}\n\nMake sure the Flask server is running:\npython app.py`);
        progressSection.style.display = 'none';
        actions.style.display = 'flex';
        compressBtn.disabled = false;
        compressBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12" />
            </svg>
            Compress All Files
        `;
    }
}

function showResults(validFiles, blob) {
    const totalOriginal = validFiles.reduce((sum, f) => sum + f.file.size, 0);
    const compressedSize = blob.size;
    const avgReduction = ((totalOriginal - compressedSize) / totalOriginal * 100).toFixed(1);

    resultsSummary.innerHTML = `
        <div class="result-row">
            <span class="result-label">Files Processed:</span>
            <span class="result-value success">${validFiles.length}</span>
        </div>
        <div class="result-row">
            <span class="result-label">Original Size:</span>
            <span class="result-value">${formatFileSize(totalOriginal)}</span>
        </div>
        <div class="result-row">
            <span class="result-label">Compressed Archive:</span>
            <span class="result-value">${formatFileSize(compressedSize)}</span>
        </div>
        <div class="result-row">
            <span class="result-label">Total Reduction:</span>
            <span class="result-value success">${avgReduction}%</span>
        </div>
    `;

    resultsSection.style.display = 'block';

    // Reset compress button
    compressBtn.disabled = false;
    compressBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12" />
        </svg>
        Compress All Files
    `;
}

function hideResults() {
    resultsSection.style.display = 'none';
    downloadBlob = null;
}

// Download Handler
downloadBtn.addEventListener('click', () => {
    if (downloadBlob) {
        const url = window.URL.createObjectURL(downloadBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'compressed_audio.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
});

// Make removeFile available globally
window.removeFile = removeFile;
