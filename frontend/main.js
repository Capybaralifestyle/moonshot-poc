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

async function runProject() {
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
    msg.textContent = 'Running agents…';
    msg.style.color = '';
    try {
        const session = await getSession();
        const headers = { 'Content-Type': 'application/json' };
        if (session) {
            headers['Authorization'] = 'Bearer ' + session.access_token;
        }
        const body = {
            description: desc,
            export_enabled: exportEnabled
        };
        const res = await fetch('/run', {
            method: 'POST',
            headers,
            body: JSON.stringify(body)
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
    document.getElementById('run-btn').addEventListener('click', runProject);
    document.getElementById('login-btn').addEventListener('click', login);
    document.getElementById('logout-btn').addEventListener('click', logout);
    // Populate history based on current auth state
    updateAuthUI();
});
