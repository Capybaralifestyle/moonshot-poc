// Client-side script for Moonshot POC SaaS

async function fetchDatasets() {
    const select = document.getElementById('dataset-select');
    select.innerHTML = '';
    try {
        const res = await fetch('/datasets');
        if (!res.ok) {
            throw new Error('Failed to fetch dataset list');
        }
        const data = await res.json();
        if (Array.isArray(data)) {
            data.forEach(id => {
                const opt = document.createElement('option');
                opt.value = id;
                opt.textContent = id;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.error(err);
    }
}

async function uploadDataset() {
    const fileInput = document.getElementById('dataset-file');
    const domainInput = document.getElementById('domain-column');
    const msg = document.getElementById('dataset-msg');
    const file = fileInput.files[0];
    if (!file) {
        msg.textContent = 'Please choose a dataset file.';
        msg.style.color = 'red';
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    const domain = domainInput.value.trim();
    if (domain) {
        formData.append('domain_column', domain);
    }
    msg.textContent = 'Uploading…';
    msg.style.color = '';
    try {
        const res = await fetch('/datasets', {
            method: 'POST',
            body: formData
        });
        if (!res.ok) {
            throw new Error('Upload failed');
        }
        const data = await res.json();
        msg.textContent = `Uploaded successfully. Dataset ID: ${data.dataset_id}`;
        msg.style.color = 'green';
        // refresh list
        await fetchDatasets();
    } catch (err) {
        msg.textContent = 'Error: ' + err.message;
        msg.style.color = 'red';
    }
}

async function runProject() {
    const select = document.getElementById('dataset-select');
    const desc = document.getElementById('description').value.trim();
    const exportEnabled = document.getElementById('export-enabled').checked;
    const msg = document.getElementById('run-msg');
    const resultsPre = document.getElementById('results');
    resultsPre.textContent = '';
    if (!desc) {
        msg.textContent = 'Please enter a project description.';
        msg.style.color = 'red';
        return;
    }
    const datasetId = select.value;
    if (!datasetId) {
        msg.textContent = 'Please select a dataset.';
        msg.style.color = 'red';
        return;
    }
    msg.textContent = 'Running agents…';
    msg.style.color = '';
    try {
        const res = await fetch('/projects/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                description: desc,
                dataset_id: datasetId,
                export_enabled: exportEnabled
            })
        });
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || 'Run failed');
        }
        const data = await res.json();
        resultsPre.textContent = JSON.stringify(data, null, 2);
        msg.textContent = 'Completed.';
        msg.style.color = 'green';
    } catch (err) {
        msg.textContent = 'Error: ' + err.message;
        msg.style.color = 'red';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('upload-btn').addEventListener('click', uploadDataset);
    document.getElementById('run-btn').addEventListener('click', runProject);
    fetchDatasets();
});