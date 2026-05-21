// Toast notification
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast ${isError ? 'error' : ''}`;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// Button animation
function animateButton(btn, state) {
    btn.classList.remove('loading', 'cross', 'check');
    if (state === 'loading') {
        btn.classList.add('loading');
    } else if (state === 'cross') {
        btn.classList.add('cross');
        setTimeout(() => btn.classList.remove('cross'), 500);
    } else if (state === 'check') {
        btn.classList.add('check');
        setTimeout(() => btn.classList.remove('check'), 500);
    }
}

// API wrapper
async function api(method, url, data = null, token = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

// Page initialization
document.addEventListener('DOMContentLoaded', function() {
    // Connect button animation
    const connectBtn = document.getElementById('connectBtn');
    if (connectBtn) {
        connectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            animateButton(this, 'loading');
            
            setTimeout(() => {
                animateButton(this, 'check');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 500);
            }, 1500);
        });
    }
    
    // Download certificate
    const certBtn = document.getElementById('certBtn');
    if (certBtn) {
        certBtn.addEventListener('click', function() {
            window.location.href = '/certificate';
            showToast('Certificate download started');
        });
    }
    
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const loginBtn = document.getElementById('loginBtn');
            const token = document.getElementById('token').value.trim();
            const password = document.getElementById('password').value.trim();
            
            if (!token || !password) {
                showToast('Please fill all fields', true);
                return;
            }
            
            animateButton(loginBtn, 'loading');
            
            const result = await api('POST', '/api/login', { token, password });
            
            if (result.success) {
                animateButton(loginBtn, 'check');
                setTimeout(() => {
                    window.location.href = `/dashboard`;
                }, 500);
            } else {
                animateButton(loginBtn, 'cross');
                showToast(result.error || 'Login failed', true);
            }
        });
    }
    
    // Dashboard timer
    if (window.remainingTime && window.remainingTime !== 'Expired') {
        updateTimerDisplay(window.remainingTime);
        startTimerCountdown();
    } else if (window.remainingTime === 'Expired') {
        document.getElementById('timer').textContent = 'EXPIRED - Contact Support';
    }
    
    // Load total users
    if (window.authToken) {
        loadTotalUsers();
        setInterval(loadTotalUsers, 5000);
    }
});

// Timer countdown
let timerInterval = null;

function parseTimeString(timeStr) {
    const parts = timeStr.match(/(\d+)d\s+(\d+)h\s+(\d+)m\s+(\d+)s/);
    if (parts) {
        return {
            days: parseInt(parts[1]),
            hours: parseInt(parts[2]),
            minutes: parseInt(parts[3]),
            seconds: parseInt(parts[4])
        };
    }
    
    const parts2 = timeStr.match(/(\d+)h\s+(\d+)m\s+(\d+)s/);
    if (parts2) {
        return {
            days: 0,
            hours: parseInt(parts2[1]),
            minutes: parseInt(parts2[2]),
            seconds: parseInt(parts2[3])
        };
    }
    
    const parts3 = timeStr.match(/(\d+)m\s+(\d+)s/);
    if (parts3) {
        return {
            days: 0,
            hours: 0,
            minutes: parseInt(parts3[1]),
            seconds: parseInt(parts3[2])
        };
    }
    
    return null;
}

function formatTimeFromSeconds(totalSeconds) {
    if (totalSeconds <= 0) return 'Expired';
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m ${seconds}s`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m ${seconds}s`;
    } else {
        return `${minutes}m ${seconds}s`;
    }
}

function updateTimerDisplay(timeStr) {
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        timerElement.textContent = timeStr;
    }
}

function startTimerCountdown() {
    if (timerInterval) clearInterval(timerInterval);
    
    let timeStruct = parseTimeString(window.remainingTime);
    if (!timeStruct) {
        if (window.remainingTime === 'Unlimited') {
            updateTimerDisplay('Unlimited Access');
            return;
        }
        return;
    }
    
    let totalSeconds = (timeStruct.days * 86400) + (timeStruct.hours * 3600) + (timeStruct.minutes * 60) + timeStruct.seconds;
    
    timerInterval = setInterval(() => {
        if (totalSeconds <= 0) {
            clearInterval(timerInterval);
            updateTimerDisplay('Expired');
            showToast('Your access has expired!', true);
            setTimeout(() => {
                window.location.href = '/login';
            }, 3000);
            return;
        }
        
        totalSeconds--;
        updateTimerDisplay(formatTimeFromSeconds(totalSeconds));
    }, 1000);
}

// Tab switching
function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.panel');
    
    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    
    if (tab === 'jwt') {
        tabs[0].classList.add('active');
        document.getElementById('jwtPanel').classList.add('active');
    } else {
        tabs[1].classList.add('active');
        document.getElementById('tokenPanel').classList.add('active');
    }
}

// Load total users
async function loadTotalUsers() {
    if (!window.authToken) return;
    
    const data = await api('GET', '/api/users', null, window.authToken);
    if (data && !data.error) {
        const totalUsers = Object.keys(data).length;
        const totalUsersElement = document.getElementById('totalUsers');
        if (totalUsersElement) {
            totalUsersElement.textContent = totalUsers;
        }
    }
}

// Save via JWT
async function saveViaJWT() {
    const uid = document.getElementById('jwtUid').value.trim();
    const jwt = document.getElementById('jwtToken').value.trim();
    
    if (!uid || !jwt) {
        showToast('Please fill both fields', true);
        return;
    }
    
    const result = await api('POST', '/api/users', { uid, jwt }, window.authToken);
    
    if (result.success) {
        showToast(result.message);
        const congratsDiv = document.getElementById('jwtCongrats');
        congratsDiv.innerHTML = '<div class="congrats">🎉 UID saved successfully! 🎉</div>';
        congratsDiv.classList.add('show');
        document.getElementById('jwtUid').value = '';
        document.getElementById('jwtToken').value = '';
        loadTotalUsers();
        setTimeout(() => congratsDiv.classList.remove('show'), 5000);
    } else {
        showToast(result.message || 'Failed to save', true);
    }
}

// Convert and save
async function convertAndSave() {
    const accessToken = document.getElementById('accessToken').value.trim();
    
    if (!accessToken) {
        showToast('Please enter Access Token', true);
        return;
    }
    
    const resultDiv = document.getElementById('tokenCongrats');
    resultDiv.innerHTML = '<div style="color:#00ff88">Converting...</div>';
    resultDiv.classList.add('show');
    
    const result = await api('POST', '/api/convert', { access_token: accessToken }, window.authToken);
    
    if (result.success) {
        resultDiv.innerHTML = `<div class="congrats">🎉 UID ${result.uid} saved successfully! 🎉</div>`;
        showToast(`User ${result.uid} saved!`);
        document.getElementById('accessToken').value = '';
        loadTotalUsers();
        setTimeout(() => resultDiv.classList.remove('show'), 5000);
    } else {
        resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
        showToast(result.error, true);
    }
}

// Show check UI
function showCheckUI() {
    const panel = document.getElementById('checkPanel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
}

// Check UID
async function checkUID() {
    const uid = document.getElementById('checkUidInput').value.trim();
    
    if (!uid) {
        showToast('Please enter UID', true);
        return;
    }
    
    const data = await api('GET', '/api/users', null, window.authToken);
    const resultDiv = document.getElementById('checkResult');
    
    if (data && data[uid]) {
        const jwt = data[uid];
        const decoded = await api('POST', '/api/decode', { token: jwt }, window.authToken);
        
        let decodedHtml = '';
        if (decoded && !decoded.error) {
            decodedHtml = `
                <hr>
                <strong>🔓 Decoded JWT:</strong>
                <div class="jwt-preview">
                    <strong>Header:</strong><br>
                    <code>${JSON.stringify(decoded.header, null, 2)}</code>
                    <br><br>
                    <strong>Payload:</strong><br>
                    <code>${JSON.stringify(decoded.payload, null, 2)}</code>
                </div>
            `;
        }
        
        resultDiv.innerHTML = `
            <div class="success">✅ UID ${uid} is registered!</div>
            <div class="jwt-preview">
                <strong>🔑 JWT Token:</strong><br>
                <code style="word-break:break-all;">${jwt}</code>
            </div>
            ${decodedHtml}
            <div class="flex-buttons" style="display: flex; gap: 10px; margin-top: 10px;">
                <button onclick="copyToClipboard('${jwt.replace(/'/g, "\\'")}')" style="background: rgba(0,255,136,0.2); border: 1px solid #00ff88; color: #00ff88; padding: 8px 16px; border-radius: 10px; cursor: pointer;">📋 Copy JWT</button>
                <button onclick="deleteUID('${uid}')" style="background: rgba(255,68,68,0.2); border: 1px solid #ff4444; color: #ff4444; padding: 8px 16px; border-radius: 10px; cursor: pointer;">🗑️ Delete UID</button>
            </div>
        `;
    } else {
        resultDiv.innerHTML = `<div class="error">❌ UID ${uid} is NOT registered</div>`;
    }
    resultDiv.classList.add('show');
}

// Delete UID
async function deleteUID(uid) {
    if (!confirm(`⚠️ Are you sure you want to delete UID ${uid}?`)) return;
    
    const result = await api('DELETE', `/api/users/${uid}`, null, window.authToken);
    
    if (result.success) {
        showToast(result.message);
        document.getElementById('checkResult').innerHTML = '';
        document.getElementById('checkResult').classList.remove('show');
        document.getElementById('checkUidInput').value = '';
        loadTotalUsers();
    } else {
        showToast('Failed to delete', true);
    }
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('JWT copied to clipboard!');
    });
}