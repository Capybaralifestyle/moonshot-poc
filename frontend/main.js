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

async function fetchAgents() {
    try {
        const res = await fetch('/agents');
        const agents = await res.json();
        const container = document.getElementById('agent-list');
        agents.forEach(agent => {
            const label = document.createElement('label');
            label.className = 'flex items-center space-x-2 cursor-pointer';
            const checked = agent === 'documentation' ? '' : 'checked';
            label.innerHTML =
                `<input type="checkbox" value="${agent}" class="sr-only peer agent-checkbox" ${checked}>` +
                `<div class=\"w-10 h-6 bg-gray-200 rounded-full peer-checked:bg-blue-600 relative transition-colors\">` +
                `<div class=\"absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-4\"></div>` +
                `</div><span class=\"capitalize\">${agent}</span>`;
            container.appendChild(label);
        });
    } catch (err) {
        console.error('Failed to load agents', err);
    }
}

async function runProject() {
    const desc = document.getElementById('description').value.trim();
    const exportEnabled = document.getElementById('export-enabled').checked;
    const msg = document.getElementById('run-msg');
    const resultsPre = document.getElementById('results');
    const progressContainer = document.getElementById('progress-container');
    resultsPre.textContent = '';
    progressContainer.innerHTML = '';

    const selectedAgents = Array.from(document.querySelectorAll('.agent-checkbox:checked')).map(cb => cb.value);
    if (!desc) {
        msg.textContent = 'Please enter a project description.';
        msg.style.color = 'red';
        return;
    }
    if (selectedAgents.length === 0) {
        msg.textContent = 'Please select at least one agent.';
        msg.style.color = 'red';
        return;
    }
    msg.textContent = 'Running agents…';
    msg.style.color = '';
    const results = {};
    try {
        const session = await getSession();
        const headers = { 'Content-Type': 'application/json' };
        if (session) {
            headers['Authorization'] = 'Bearer ' + session.access_token;
        }
        for (const agent of selectedAgents) {
            const card = document.createElement('div');
            card.className = 'bg-white p-4 rounded-lg shadow';
            card.innerHTML = `<h3 class="font-medium mb-2">${agent}</h3>` +
                `<div class="w-full bg-gray-200 rounded-full h-2"><div class="bg-blue-500 h-2 rounded-full" id="bar-${agent}" style="width:0%"></div></div>`;
            progressContainer.appendChild(card);

            const body = {
                description: desc,
                export_enabled: exportEnabled,
                agents: [agent]
            };
            const res = await fetch('/run', {
                method: 'POST',
                headers,
                body: JSON.stringify(body)
            });
            if (!res.ok) {
                const text = await res.text();
                throw new Error(text || `Run failed for ${agent}`);
            }
            const data = await res.json();
            results[agent] = data.results[agent];
            document.getElementById(`bar-${agent}`).style.width = '100%';
        }
        resultsPre.textContent = JSON.stringify(results, null, 2);
        msg.textContent = 'Completed.';
        msg.style.color = 'green';
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
        loginBtn.classList.add('hidden');
        logoutBtn.classList.remove('hidden');
        authInfo.textContent = session.user.email || session.user.id;
        appContent.classList.remove('hidden');
        await fetchHistory();
    } else {
        loginBtn.classList.remove('hidden');
        logoutBtn.classList.add('hidden');
        authInfo.textContent = '';
        appContent.classList.add('hidden');
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
    fetchAgents();
});
