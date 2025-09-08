// dashboard.js - Xử lý dashboard và navigation
let currentPage = 'dashboard';

// Hiển thị trang   
function showPage(pageName) {
    // Ẩn tất cả các trang
    const pages = ['dashboard', 'employees', 'addEmployee', 'attendance'];
    pages.forEach(page => {
        document.getElementById(`${page}Page`).classList.add('hidden');
    });
    
    // Hiển thị trang được chọn
    document.getElementById(`${pageName}Page`).classList.remove('hidden');
    
    // Cập nhật active navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('bg-blue-50', 'text-blue-600');
        item.classList.add('text-gray-700');
    });
    
    // Active item hiện tại
    event?.target.closest('.nav-item')?.classList.add('bg-blue-50', 'text-blue-600');
    event?.target.closest('.nav-item')?.classList.remove('text-gray-700');
    
    // Cập nhật tiêu đề trang
    const titles = {
        dashboard: 'Dashboard',
        employees: 'Quản lý nhân viên',
        addEmployee: 'Thêm nhân viên mới',
        attendance: 'Lịch sử chấm công'
    };
    document.getElementById('pageTitle').textContent = titles[pageName] || 'Dashboard';
    
    currentPage = pageName;
    
    // Load dữ liệu cho trang tương ứng
    switch(pageName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'employees':
            loadEmployees();
            break;
        case 'attendance':
            loadAttendance();
            break;
    }
}

// Load dữ liệu dashboard
async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
            headers: getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (data.success) {
            const stats = data.data;
            
            // Cập nhật số liệu thống kê
            document.getElementById('totalEmployees').textContent = stats.total_employees || 0;
            document.getElementById('presentToday').textContent = stats.present_today || 0;
            document.getElementById('absentToday').textContent = stats.absent_today || 0;
            document.getElementById('lateToday').textContent = stats.late_today || 0;
            
            // Cập nhật lịch sử chấm công gần đây
            updateRecentAttendance(stats.recent_attendance || []);
        } else {
            showNotification(data.message || 'Không thể tải dữ liệu dashboard', 'error');
        }
    } catch (error) {
        console.error('Load dashboard error:', error);
        showNotification('Lỗi khi tải dữ liệu dashboard', 'error');
    }
}

// Cập nhật danh sách chấm công gần đây
function updateRecentAttendance(attendanceList) {
    const container = document.getElementById('recentAttendance');
    
    if (!attendanceList || attendanceList.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">Chưa có dữ liệu chấm công</p>';
        return;
    }
    
    container.innerHTML = attendanceList.map(record => {
        const time = new Date(record.check_time).toLocaleString('vi-VN');
        const statusClass = getStatusClass(record.work_status);
        const checkTypeLabel = record.check_type === 'checkin' ? 'Checkin' : 'Checkout';
        
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-user text-blue-600 text-sm"></i>
                    </div>
                    <div class="flex flex-col">
                        <p class="font-medium text-gray-800 text-lg">${record.employee_name || record.employee_code}</p>
                        <p class="text-sm text-gray-600">${time}</p>
                    </div>
                </div>

                <div class="flex flex-row items-center space-x-3">
                    <!-- Check-in / Check-out -->
                    <span class="px-3 py-1 rounded-full text-lg font-bold 
                        ${checkTypeLabel === 'Checkin' ? 'bg-green-100 text-green-500' : 'bg-red-100 text-red-500'}">
                        ${checkTypeLabel}
                    </span>

                    <!-- Trạng thái làm việc với background -->
                    <span class="px-3 py-1 rounded-full text-lg font-semibold
                        ${record.work_status === 'present' ? 'bg-green-100 text-green-500' : ''}
                        ${record.work_status === 'late' ? 'bg-red-100 text-red-500' : ''}
                        ${record.work_status !== 'present' && record.work_status !== 'late' ? 'bg-gray-100 text-gray-500    ' : ''}">
                        ${record.work_status || ''}
                    </span>
                </div>
            </div>

        `;
    }).join('');
}

function getStatusClass(status) {
    switch (status) {
        case 'Có mặt':
        case 'Đúng giờ':
            return 'bg-green-100 text-green-800';
        case 'Đi muộn':
            return 'bg-yellow-100 text-yellow-800';
        case 'Vắng mặt':
            return 'bg-red-100 text-red-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}


function formatDateForInput(date) {
    return date.toISOString().split('T')[0];
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('vi-VN');
}

function formatTime(dateString) {
    return new Date(dateString).toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

let dashboardInterval;

function startDashboardAutoRefresh() {
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
    }
    
    dashboardInterval = setInterval(() => {
        if (currentPage === 'dashboard') {
            loadDashboardData();
        }
    }, 30000); 
}

function stopDashboardAutoRefresh() {
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
        dashboardInterval = null;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    startDashboardAutoRefresh();
});

document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopDashboardAutoRefresh();
    } else {
        startDashboardAutoRefresh();
    }
});

window.showPage = showPage;
window.loadDashboardData = loadDashboardData;