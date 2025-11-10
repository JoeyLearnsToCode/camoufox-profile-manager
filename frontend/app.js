// Camoufox Profile Manager - Frontend Logic

// ========== Internationalization System ==========
let translations = {};
let currentLang = 'zh';

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
let fullscreenEl, proxyProtocolEl, proxyEnabledEl, proxyHostEl, proxyPortEl, proxyUsernameEl, proxyPasswordEl;
let useGeoipEl, persistentDirEl, storageEnabledEl, statusMessageEl;
let newProfileBtn, deleteProfileBtn, saveBtn, launchBtn, stopBtn;
let themeToggleBtn, langToggleBtn;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    // Get DOM references
    profileListEl = document.getElementById('profileList');
    profileNameEl = document.getElementById('profileName');
    viewportWidthEl = document.getElementById('viewportWidth');
    viewportHeightEl = document.getElementById('viewportHeight');
    fullscreenEl = document.getElementById('fullscreen');
    proxyProtocolEl = document.getElementById('proxyProtocol');
    proxyEnabledEl = document.getElementById('proxyEnabled');
    proxyHostEl = document.getElementById('proxyHost');
    proxyPortEl = document.getElementById('proxyPort');
    proxyUsernameEl = document.getElementById('proxyUsername');
    proxyPasswordEl = document.getElementById('proxyPassword');
    useGeoipEl = document.getElementById('useGeoip');
    persistentDirEl = document.getElementById('persistentDir');
    storageEnabledEl = document.getElementById('storageEnabled');
    statusMessageEl = document.getElementById('statusMessage');
    
    newProfileBtn = document.getElementById('newProfileBtn');
    deleteProfileBtn = document.getElementById('deleteProfileBtn');
    saveBtn = document.getElementById('saveBtn');
    launchBtn = document.getElementById('launchBtn');
    stopBtn = document.getElementById('stopBtn');
    themeToggleBtn = document.getElementById('themeToggle');
    langToggleBtn = document.getElementById('langToggle');
    
    // Load theme
    loadTheme();
    
    // Detect and load language (synchronously initialize)
    currentLang = detectLanguage();
    if (currentLang === 'en') {
        try {
            const response = await fetch('/translations/en.json');
            if (response.ok) {
                translations = await response.json();
            }
        } catch (error) {
            console.warn('Failed to load translations:', error);
        }
    }
    updateLanguageButton();
    
    // Update initial UI texts
    updateStaticTexts();
    
    // Event listeners
    newProfileBtn.addEventListener('click', createProfile);
    deleteProfileBtn.addEventListener('click', deleteProfile);
    saveBtn.addEventListener('click', saveProfile);
    launchBtn.addEventListener('click', launchSession);
    stopBtn.addEventListener('click', stopSession);
    themeToggleBtn.addEventListener('click', toggleTheme);
    langToggleBtn.addEventListener('click', toggleLanguage);
    
    // Fullscreen mode: disable/enable viewport inputs
    fullscreenEl.addEventListener('change', () => {
        const isFullscreen = fullscreenEl.checked;
        viewportWidthEl.disabled = isFullscreen;
        viewportHeightEl.disabled = isFullscreen;
    });
    
    // Proxy enabled: disable/enable proxy config inputs
    proxyEnabledEl.addEventListener('change', () => {
        const isEnabled = proxyEnabledEl.checked;
        proxyProtocolEl.disabled = !isEnabled;
        proxyHostEl.disabled = !isEnabled;
        proxyPortEl.disabled = !isEnabled;
        proxyUsernameEl.disabled = !isEnabled;
        proxyPasswordEl.disabled = !isEnabled;
        useGeoipEl.disabled = !isEnabled;
    });
    
    // Storage enabled: disable/enable storage directory input
    storageEnabledEl.addEventListener('change', () => {
        const isEnabled = storageEnabledEl.checked;
        persistentDirEl.disabled = !isEnabled;
    });
    
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
        showStatus(`${t('错误')}: ${error.message}`, 'error');
        updateState({ loading: false });
    }
}

async function createProfile() {
    const profileCount = state.profiles.length + 1;
    const newProfile = {
        name: `${t('配置文件')} ${profileCount}`,
        viewport_width: 1280,
        viewport_height: 800,
        fullscreen: false,
        persistent_dir: `D:\\Data\\Profile ${profileCount}`,
        storage_enabled: true,
        use_geoip: false,
        proxy: {
            protocol: "socks5",
            host: "127.0.0.1",
            port: 7888,
            username: "",
            password: "",
            enabled: false
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
            throw new Error(error.message || t('创建失败'));
        }
        
        const created = await res.json();
        showStatus(t('配置文件已创建'), 'success');
        await loadProfiles();
        selectProfile(created);
    } catch (error) {
        showStatus(`${t('错误')}: ${error.message}`, 'error');
    }
}

async function saveProfile() {
    if (!state.selectedProfile) {
        showStatus(t('未选择配置文件'), 'error');
        return;
    }
    
    const updated = {
        name: profileNameEl.value.trim(),
        viewport_width: parseInt(viewportWidthEl.value),
        viewport_height: parseInt(viewportHeightEl.value),
        fullscreen: fullscreenEl.checked,
        persistent_dir: persistentDirEl.value.trim(),
        storage_enabled: storageEnabledEl.checked,
        use_geoip: useGeoipEl.checked,
        proxy: {
            protocol: proxyProtocolEl.value,
            enabled: proxyEnabledEl.checked,
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
            throw new Error(error.message || t('保存失败'));
        }
        
        showStatus(t('配置文件已保存'), 'success');
        await loadProfiles();
        selectProfile(updated);
    } catch (error) {
        showStatus(`${t('错误')}: ${error.message}`, 'error');
    }
}

async function deleteProfile() {
    if (!state.selectedProfile) {
        showStatus(t('未选择配置文件'), 'error');
        return;
    }
    
    if (!confirm(t('确认删除配置文件') + ` '${state.selectedProfile.name}'?`)) {
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/profiles/${state.selectedProfile.name}`, {
            method: 'DELETE'
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || t('删除失败'));
        }
        
        showStatus(t('配置文件已删除'), 'success');
        updateState({ selectedProfile: null });
        await loadProfiles();
    } catch (error) {
        showStatus(`${t('错误')}: ${error.message}`, 'error');
    }
}

async function launchSession() {
    if (!state.selectedProfile) {
        showStatus(t('未选择配置文件'), 'error');
        return;
    }
    
    const payload = {
        profile_name: state.selectedProfile.name
    };
    
    // Fullscreen mode: pass screen dimensions
    if (state.selectedProfile.fullscreen) {
        payload.screen_width = window.screen.width;
        payload.screen_height = window.screen.height;
    }
    
    try {
        const res = await fetch(`${API_BASE}/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || t('启动失败'));
        }
        
        const session = await res.json();
        updateState({ session });
        showStatus(`${t('会话已启动')}: ${state.selectedProfile.name}`, 'success');
    } catch (error) {
        showStatus(`${t('错误')}: ${error.message}`, 'error');
    }
}

async function stopSession() {
    try {
        const res = await fetch(`${API_BASE}/session`, {
            method: 'DELETE'
        });
        
        if (!res.ok && res.status !== 404) {
            const error = await res.json();
            throw new Error(error.message || t('停止失败'));
        }
        
        updateState({ session: null });
        showStatus(t('会话已停止'), 'info');
    } catch (error) {
        showStatus(`${t('错误')}: ${error.message}`, 'error');
    }
}

async function checkSessionStatus() {
    try {
        const res = await fetch(`${API_BASE}/session`);
        
        if (res.ok) {
            const session = await res.json();
            // Check if session is null (no active session)
            if (session === null) {
                if (state.session) {
                    updateState({ session: null });
                    showStatus(t('会话已结束'), 'info');
                }
            } else if (!state.session) {
                updateState({ session });
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
        proxyProtocolEl.value = 'socks5';
        proxyEnabledEl.checked = false;
        proxyHostEl.value = '';
        proxyPortEl.value = '';
        proxyUsernameEl.value = '';
        proxyPasswordEl.value = '';
        useGeoipEl.checked = false;
        persistentDirEl.value = '';
        storageEnabledEl.checked = true;
        return;
    }
    
    const p = state.selectedProfile;
    profileNameEl.value = p.name;
    viewportWidthEl.value = p.viewport_width;
    viewportHeightEl.value = p.viewport_height;
    fullscreenEl.checked = p.fullscreen;
    // Sync viewport input disabled state with fullscreen
    viewportWidthEl.disabled = p.fullscreen;
    viewportHeightEl.disabled = p.fullscreen;
    proxyProtocolEl.value = p.proxy.protocol || 'socks5';
    proxyEnabledEl.checked = p.proxy.enabled || false;
    // Sync proxy inputs disabled state with proxy enabled
    const proxyEnabled = p.proxy.enabled || false;
    proxyProtocolEl.disabled = !proxyEnabled;
    proxyHostEl.disabled = !proxyEnabled;
    proxyPortEl.disabled = !proxyEnabled;
    proxyUsernameEl.disabled = !proxyEnabled;
    proxyPasswordEl.disabled = !proxyEnabled;
    useGeoipEl.disabled = !proxyEnabled;
    proxyHostEl.value = p.proxy.host || '';
    proxyPortEl.value = p.proxy.port || '';
    proxyUsernameEl.value = p.proxy.username || '';
    proxyPasswordEl.value = p.proxy.password || '';
    useGeoipEl.checked = p.use_geoip;
    persistentDirEl.value = p.persistent_dir;
    storageEnabledEl.checked = p.storage_enabled !== undefined ? p.storage_enabled : true;
    // Sync storage directory disabled state with storage enabled
    persistentDirEl.disabled = !storageEnabledEl.checked;
}

function updateButtonStates() {
    const hasProfile = !!state.selectedProfile;
    const sessionRunning = !!state.session;
    
    // Disable editing controls during session, enable when session=null
    deleteProfileBtn.disabled = sessionRunning;
    saveBtn.disabled = sessionRunning;
    profileNameEl.disabled = sessionRunning;
    // Viewport inputs: disabled if session running OR fullscreen enabled
    const fullscreenEnabled = state.selectedProfile?.fullscreen || false;
    viewportWidthEl.disabled = sessionRunning || fullscreenEnabled;
    viewportHeightEl.disabled = sessionRunning || fullscreenEnabled;
    fullscreenEl.disabled = sessionRunning;
    
    // Proxy controls
    proxyEnabledEl.disabled = sessionRunning;
    const proxyEnabled = state.selectedProfile?.proxy?.enabled || false;
    proxyProtocolEl.disabled = sessionRunning || !proxyEnabled;
    proxyHostEl.disabled = sessionRunning || !proxyEnabled;
    proxyPortEl.disabled = sessionRunning || !proxyEnabled;
    proxyUsernameEl.disabled = sessionRunning || !proxyEnabled;
    proxyPasswordEl.disabled = sessionRunning || !proxyEnabled;
    useGeoipEl.disabled = sessionRunning || !proxyEnabled;
    
    // Storage controls
    storageEnabledEl.disabled = sessionRunning;
    const storageEnabled = state.selectedProfile?.storage_enabled !== undefined ? state.selectedProfile.storage_enabled : true;
    persistentDirEl.disabled = sessionRunning || !storageEnabled;
    
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
    statusMessageEl.style.color = '';  // Clear inline style to use class color
    
    // Clear after 5 seconds
    setTimeout(() => {
        if (statusMessageEl.textContent === message) {
            statusMessageEl.textContent = t('就绪');
            statusMessageEl.className = '';
            statusMessageEl.style.color = 'var(--text-secondary)';
        }
    }, 5000);
}

// ========== Theme System ==========
function loadTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark');
        document.documentElement.classList.add('dark');
    }
    updateThemeButton();
}

function toggleTheme() {
    const isDark = document.body.classList.toggle('dark');
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeButton();
}

function updateThemeButton() {
    const isDark = document.body.classList.contains('dark');
    themeToggleBtn.textContent = isDark ? '🌙' : '🌞';
}

// ========== Internationalization System ==========
async function loadTranslations() {
    try {
        const response = await fetch('/translations/en.json');
        translations = await response.json();
    } catch (error) {
        console.warn('Failed to load translations:', error);
    }
}

function t(chineseText) {
    if (currentLang === 'zh') return chineseText;
    return translations[chineseText] || chineseText;
}

function detectLanguage() {
    const saved = localStorage.getItem('language');
    if (saved) return saved;
    
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('zh')) return 'zh';
    if (browserLang.startsWith('en')) return 'en';
    return 'zh'; // Default to Chinese
}

async function toggleLanguage() {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('language', currentLang);
    
    // Load translations if switching to English
    if (currentLang === 'en' && Object.keys(translations).length === 0) {
        try {
            const response = await fetch('/translations/en.json');
            if (response.ok) {
                translations = await response.json();
            }
        } catch (error) {
            console.warn('Failed to load translations:', error);
        }
    }
    
    updateUITexts();
    updateStaticTexts();
    updateLanguageButton();
}

function updateLanguageButton() {
    // Display current language, not the target language
    langToggleBtn.textContent = currentLang === 'zh' ? '中' : 'EN';
}

function updateUITexts() {
    // Update page title
    document.title = t('Camoufox 配置文件');
    
    // Re-render dynamic content
    render();
}

function updateStaticTexts() {
    // Update page title
    document.title = t('Camoufox 配置文件');
    
    // Update button texts
    newProfileBtn.textContent = t('新建配置');
    deleteProfileBtn.textContent = t('删除');
    saveBtn.textContent = t('保存更改');
    launchBtn.textContent = t('启动会话');
    stopBtn.textContent = t('停止会话');
    
    // Update h1 title
    const h1 = document.querySelector('h1');
    if (h1) h1.textContent = t('Camoufox 配置文件');
    
    // Update all labels with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = t(key);
    });
    
    // Update placeholders
    profileNameEl.placeholder = t('配置文件名称');
    proxyHostEl.placeholder = '127.0.0.1';
    proxyPortEl.placeholder = '7888';
    
    // Update status message if it's in default state
    if (statusMessageEl.textContent === 'Ready' || statusMessageEl.textContent === '就绪') {
        statusMessageEl.textContent = t('就绪');
    }
}
