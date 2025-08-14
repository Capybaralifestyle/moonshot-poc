// Client-side script for Moonshot POC SaaS with Supabase authentication and persistence

// -----------------------------------------------------------------------------
// Configuration
// Replace the placeholders below with your Supabase project URL and anonymous key.
// Without valid values, authentication will not work.  These values are NOT
// automatically injected; you must set them when deploying the frontend.
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// Initialise the Supabase client.  The global "supabase" comes from the
// included UMD build of @supabase/supabase-js.  See index.html for the import.
const supa = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// -----------------------------------------------------------------------------
// Helper functions

async function getSession() {
    // Retrieves the current session (if any) from Supabase.
    const { data } = await supa.auth.getSession();
    return data.session || null;
}

async function fetchDatasets() {
    const select = document.getElementById('dataset-select');
    select.innerHTML = '';
    try {
        const session = await getSession();
        const headers = {};
        if (session) {
            headers['Authorization'] = 'Bearer ' + session.access_token;
        }
        const res = await fetch('/datasets', { headers });
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
        const session = await getSession();
        const headers = {};
        if (session) {
            headers['Authorization'] = 'Bearer ' + session.access_token;
        }
        const res = await fetch('/datasets', {
            method: 'POST',
            headers,
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
        const session = await getSession();
        const headers = { 'Content-Type': 'application/json' };
        if (session) {
            headers['Authorization'] = 'Bearer ' + session.access_token;
        }
        const res = await fetch('/projects/run', {
            method: 'POST',
            headers,
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
        // Refresh history after a successful run
        await fetchHistory();
    } catch (err) {
        msg.textContent = 'Error: ' + err.message;
        msg.style.color = 'red';
    }
}

// Fetch and display the latest runs for the authenticated user
async function fetchHistory() {
    const historyPre = document.getElementById('history');
    historyPre.textContent = '';
    try {
        const session = await getSession();
        if (!session) {
            return;
        }
        const res = await fetch('/projects/latest', {
            headers: { 'Authorization': 'Bearer ' + session.access_token }
        });
        if (!res.ok) {
            throw new Error('Failed to fetch history');
        }
        const data = await res.json();
        historyPre.textContent = JSON.stringify(data.runs, null, 2);
    } catch (err) {
        console.error(err);
        historyPre.textContent = 'Error loading history';
    }
}

// Authentication UI handlers
async function login() {
    // Trigger Google OAuth sign-in via Supabase.  Supabase will handle the
    // redirect; once the user is logged in, the access token is stored in
    // local storage automatically.
    await supa.auth.signInWithOAuth({ provider: 'google' });
}

async function logout() {
    await supa.auth.signOut();
    // Update UI after sign-out
    updateAuthUI();
}

// Update the UI based on authentication state
async function updateAuthUI() {
    const session = await getSession();
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const authInfo = document.getElementById('auth-info');
    const appContent = document.getElementById('app-content');
    if (session && session.user) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-block';
        authInfo.textContent = session.user.email || session.user.id;
        appContent.style.display = 'block';
        await fetchDatasets();
        await fetchHistory();
    } else {
        loginBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
        authInfo.textContent = '';
        appContent.style.display = 'none';
    }
}

// Listen for auth state changes and update UI accordingly
supa.auth.onAuthStateChange(() => {
    updateAuthUI();
});

// Initialise event listeners once the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('upload-btn').addEventListener('click', uploadDataset);
    document.getElementById('run-btn').addEventListener('click', runProject);
    document.getElementById('login-btn').addEventListener('click', login);
    document.getElementById('logout-btn').addEventListener('click', logout);
    // Populate datasets and history based on current auth state
    updateAuthUI();
});