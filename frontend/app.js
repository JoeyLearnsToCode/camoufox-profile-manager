// Camoufox Profile Manager - Frontend Logic

// Centralized state
const state = {
    profiles: [],
    selectedProfile: null,
    session: null,
    loading: false
};

// API base URL
const API_BASE = '/api';

// DOM elements
let profileListEl, profileNameEl, viewportWidthEl, viewportHeightEl;
let fullscreenEl, proxyHostEl, proxyPortEl, proxyUsernameEl, proxyPasswordEl;
let useGeoipEl, persistentDirEl, statusMessageEl;
let newProfileBtn, deleteProfileBtn, saveBtn, launchBtn, stopBtn;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM references
    profileListEl = document.getElementById('profileList');
    profileNameEl = document.getElementById('profileName');
    viewportWidthEl = document.getElementById('viewportWidth');
    viewportHeightEl = document.getElementById('viewportHeight');
    fullscreenEl = document.getElementById('fullscreen');
    proxyHostEl = document.getElementById('proxyHost');
    proxyPortEl = document.getElementById('proxyPort');
    proxyUsernameEl = document.getElementById('proxyUsername');
    proxyPasswordEl = document.getElementById('proxyPassword');
    useGeoipEl = document.getElementById('useGeoip');
    persistentDirEl = document.getElementById('persistentDir');
    statusMessageEl = document.getElementById('statusMessage');
    
    newProfileBtn = document.getElementById('newProfileBtn');
    deleteProfileBtn = document.getElementById('deleteProfileBtn');
    saveBtn = document.getElementById('saveBtn');
    launchBtn = document.getElementById('launchBtn');
    stopBtn = document.getElementById('stopBtn');
    
    // Event listeners
    newProfileBtn.addEventListener('click', createProfile);
    deleteProfileBtn.addEventListener('click', deleteProfile);
    saveBtn.addEventListener('click', saveProfile);
    launchBtn.addEventListener('click', launchSession);
    stopBtn.addEventListener('click', stopSession);
    
    // Load initial data
    loadProfiles();
    
    // Poll session status
    setInterval(checkSessionStatus, 2000);
});

// State management
function updateState(newState) {
    Object.assign(state, newState);
    render();
}

function render() {
    renderProfileList();
    renderProfileDetail();
    updateButtonStates();
}

// API calls
async function loadProfiles() {
    try {
        updateState({ loading: true });
        const res = await fetch(`${API_BASE}/profiles`);
        const profiles = await res.json();
        updateState({ profiles, loading: false });
        
        // Select first profile if none selected
        if (!state.selectedProfile && profiles.length > 0) {
            selectProfile(profiles[0]);
        }
    } catch (error) {
        showStatus(`Error loading profiles: ${error.message}`, 'error');
        updateState({ loading: false });
    }
}

async function createProfile() {
    const profileCount = state.profiles.length + 1;
    const newProfile = {
        name: `Profile ${profileCount}`,
        viewport_width: 1280,
        viewport_height: 800,
        fullscreen: false,
        persistent_dir: `C:\\Profile ${profileCount}`,
        use_geoip: false,
        proxy: {
            host: "",
            port: 0,
            username: "",
            password: ""
        }
    };
    
    try {
        const res = await fetch(`${API_BASE}/profiles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newProfile)
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || 'Failed to create profile');
        }
        
        const created = await res.json();
        showStatus('Profile created successfully', 'success');
        await loadProfiles();
        selectProfile(created);
    } catch (error) {
        showStatus(`Error creating profile: ${error.message}`, 'error');
    }
}

async function saveProfile() {
    if (!state.selectedProfile) {
        showStatus('No profile selected', 'error');
        return;
    }
    
    const updated = {
        name: profileNameEl.value.trim(),
        viewport_width: parseInt(viewportWidthEl.value),
        viewport_height: parseInt(viewportHeightEl.value),
        fullscreen: fullscreenEl.checked,
        persistent_dir: persistentDirEl.value.trim(),
        use_geoip: useGeoipEl.checked,
        proxy: {
            host: proxyHostEl.value.trim(),
            port: parseInt(proxyPortEl.value) || 0,
            username: proxyUsernameEl.value.trim(),
            password: proxyPasswordEl.value.trim()
        }
    };
    
    try {
        const res = await fetch(`${API_BASE}/profiles/${state.selectedProfile.name}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updated)
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || 'Failed to save profile');
        }
        
        showStatus('Profile saved successfully', 'success');
        await loadProfiles();
        selectProfile(updated);
    } catch (error) {
        showStatus(`Error saving profile: ${error.message}`, 'error');
    }
}

async function deleteProfile() {
    if (!state.selectedProfile) {
        showStatus('No profile selected', 'error');
        return;
    }
    
    if (!confirm(`Delete profile '${state.selectedProfile.name}'?`)) {
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/profiles/${state.selectedProfile.name}`, {
            method: 'DELETE'
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || 'Failed to delete profile');
        }
        
        showStatus('Profile deleted successfully', 'success');
        updateState({ selectedProfile: null });
        await loadProfiles();
    } catch (error) {
        showStatus(`Error deleting profile: ${error.message}`, 'error');
    }
}

async function launchSession() {
    if (!state.selectedProfile) {
        showStatus('No profile selected', 'error');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_name: state.selectedProfile.name })
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || 'Failed to start session');
        }
        
        const session = await res.json();
        updateState({ session });
        showStatus(`Session started for '${state.selectedProfile.name}'`, 'success');
    } catch (error) {
        showStatus(`Error starting session: ${error.message}`, 'error');
    }
}

async function stopSession() {
    try {
        const res = await fetch(`${API_BASE}/session`, {
            method: 'DELETE'
        });
        
        if (!res.ok && res.status !== 404) {
            const error = await res.json();
            throw new Error(error.message || 'Failed to stop session');
        }
        
        updateState({ session: null });
        showStatus('Session stopped', 'info');
    } catch (error) {
        showStatus(`Error stopping session: ${error.message}`, 'error');
    }
}

async function checkSessionStatus() {
    try {
        const res = await fetch(`${API_BASE}/session`);
        
        if (res.ok) {
            const session = await res.json();
            if (!state.session) {
                updateState({ session });
            }
        } else {
            if (state.session) {
                updateState({ session: null });
            }
        }
    } catch (error) {
        // Silently fail - session check is background task
    }
}

// Rendering functions
function renderProfileList() {
    profileListEl.innerHTML = '';
    
    state.profiles.forEach(profile => {
        const item = document.createElement('div');
        item.className = 'profile-item';
        if (state.selectedProfile && profile.name === state.selectedProfile.name) {
            item.classList.add('selected');
        }
        item.textContent = profile.name;
        item.addEventListener('click', () => selectProfile(profile));
        profileListEl.appendChild(item);
    });
}

function renderProfileDetail() {
    if (!state.selectedProfile) {
        // Clear form
        profileNameEl.value = '';
        viewportWidthEl.value = '';
        viewportHeightEl.value = '';
        fullscreenEl.checked = false;
        proxyHostEl.value = '';
        proxyPortEl.value = '';
        proxyUsernameEl.value = '';
        proxyPasswordEl.value = '';
        useGeoipEl.checked = false;
        persistentDirEl.value = '';
        return;
    }
    
    const p = state.selectedProfile;
    profileNameEl.value = p.name;
    viewportWidthEl.value = p.viewport_width;
    viewportHeightEl.value = p.viewport_height;
    fullscreenEl.checked = p.fullscreen;
    proxyHostEl.value = p.proxy.host || '';
    proxyPortEl.value = p.proxy.port || '';
    proxyUsernameEl.value = p.proxy.username || '';
    proxyPasswordEl.value = p.proxy.password || '';
    useGeoipEl.checked = p.use_geoip;
    persistentDirEl.value = p.persistent_dir;
}

function updateButtonStates() {
    const hasProfile = !!state.selectedProfile;
    const sessionRunning = !!state.session;
    
    // Disable editing controls during session
    deleteProfileBtn.disabled = sessionRunning;
    saveBtn.disabled = sessionRunning;
    profileNameEl.disabled = sessionRunning;
    viewportWidthEl.disabled = sessionRunning;
    viewportHeightEl.disabled = sessionRunning;
    fullscreenEl.disabled = sessionRunning;
    proxyHostEl.disabled = sessionRunning;
    proxyPortEl.disabled = sessionRunning;
    proxyUsernameEl.disabled = sessionRunning;
    proxyPasswordEl.disabled = sessionRunning;
    useGeoipEl.disabled = sessionRunning;
    persistentDirEl.disabled = sessionRunning;
    newProfileBtn.disabled = sessionRunning;
    
    // Session controls
    launchBtn.disabled = !hasProfile || sessionRunning;
    stopBtn.disabled = !sessionRunning;
}

function selectProfile(profile) {
    updateState({ selectedProfile: profile });
}

function showStatus(message, type = 'info') {
    statusMessageEl.textContent = message;
    statusMessageEl.className = `status-${type}`;
    
    // Clear after 5 seconds
    setTimeout(() => {
        if (statusMessageEl.textContent === message) {
            statusMessageEl.textContent = 'Ready';
            statusMessageEl.className = 'text-gray-400';
        }
    }, 5000);
}
