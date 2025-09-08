// auth.js - Xử lý đăng nhập và xác thực
const API_BASE_URL = 'http://localhost:5000/api';

// Lưu token vào localStorage
function saveToken(token) {
    localStorage.setItem('auth_token', token);
}

// Lấy token từ localStorage
function getToken() {
    return localStorage.getItem('auth_token');
}

// Xóa token khỏi localStorage
function removeToken() {
    localStorage.removeItem('auth_token');
}

// Kiểm tra xem user đã đăng nhập chưa
function isAuthenticated() {
    const token = getToken();
    if (!token) return false;
    
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp > Date.now() / 1000;
    } catch (e) {
        return false;
    }
}

// Thêm token vào header của request
function getAuthHeaders() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Hiển thị trang đăng nhập
function showLogin() {
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('registerPage').classList.add('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

// Hiển thị trang đăng ký
function showRegister() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('registerPage').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

// Hiển thị ứng dụng chính
function showMainApp() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('registerPage').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    
    // Load dashboard mặc định
    showPage('dashboard');
    loadDashboardData();
}

// Xử lý đăng nhập
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showNotification('Vui lòng nhập đầy đủ thông tin', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            saveToken(data.token);
            showNotification('Đăng nhập thành công!', 'success');
            setTimeout(showMainApp, 1000);
        } else {
            showNotification(data.message || 'Đăng nhập thất bại', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Lỗi kết nối server', 'error');
    }
});

// Xử lý đăng ký
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    
    if (!username || !password || !confirmPassword) {
        showNotification('Vui lòng nhập đầy đủ thông tin', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showNotification('Mật khẩu xác nhận không khớp', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Đăng ký thành công! Vui lòng đăng nhập', 'success');
            setTimeout(showLogin, 1000);
        } else {
            showNotification(data.message || 'Đăng ký thất bại', 'error');
        }
    } catch (error) {
        console.error('Register error:', error);
        showNotification('Lỗi kết nối server', 'error');
    }
});

// Đăng xuất
function logout() {
    removeToken();
    showNotification('Đã đăng xuất', 'info');
    showLogin();
}

// Hiển thị thông báo
function showNotification(message, type = 'info') {
    // Tạo element thông báo
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ${getNotificationClass(type)}`;
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-lg">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove sau 5 giây
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationClass(type) {
    switch (type) {
        case 'success': return 'bg-green-500 text-white';
        case 'error': return 'bg-red-500 text-white';
        case 'warning': return 'bg-yellow-500 text-white';
        default: return 'bg-blue-500 text-white';
    }
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        default: return 'fa-info-circle';
    }
}

// Kiểm tra authentication khi trang load
document.addEventListener('DOMContentLoaded', function() {
    if (isAuthenticated()) {
        showMainApp();
    } else {
        showLogin();
    }
    
    // Update thời gian hiện tại
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});

// Cập nhật thời gian hiện tại
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}