// attendance.js - Quản lý lịch sử chấm công
let attendanceData = [];

function mapStatus(status) {
    switch (status) {
        case 'present':
            return { label: 'Đúng giờ', class: 'bg-green-100 text-green-800' };
        case 'late':
            return { label: 'Đi muộn', class: 'bg-yellow-100 text-yellow-800' };
        case 'early':
            return { label: 'Về sớm', class: 'bg-purple-100 text-purple-800' };
        case 'absent':
            return { label: 'Vắng mặt', class: 'bg-red-100 text-red-800' };
        default:
            return { label: 'Không rõ', class: 'bg-gray-100 text-gray-800' };
    }
}

// Load lịch sử chấm công
async function loadAttendance() {
    try {
        const dateFilter = document.getElementById('dateFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;

        let url = `${API_BASE_URL}/attendance`;
        const params = new URLSearchParams();

        if (dateFilter) params.append('date', dateFilter);
        if (statusFilter) params.append('status', statusFilter);

        if (params.toString()) {
            url += '?' + params.toString();
        }

        const response = await fetch(url, {
            headers: getAuthHeaders()
        });

        const data = await response.json();

        if (data.success) {
            attendanceData = data.data;
            renderAttendanceTable(attendanceData);
        } else {
            showNotification(data.message || 'Không thể tải lịch sử chấm công', 'error');
        }
    } catch (error) {
        console.error('Load attendance error:', error);
        showNotification('Lỗi khi tải lịch sử chấm công', 'error');
    }
}

// Render bảng lịch sử chấm công
function renderAttendanceTable(attendance) {
    const tbody = document.getElementById('attendanceTableBody');

    if (!attendance || attendance.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center text-gray-500">
                    Không có dữ liệu chấm công
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = attendance.map(record => {
        const checkinTime = record.checkin_time || '--:--';
        const checkoutTime = record.checkout_time || '--:--';
        const { label, class: statusClass } = mapStatus(record.status);

        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">${formatDate(record.date)}</td>
                <td class="px-6 py-4 whitespace-nowrap">${record.employee_code}</td>
                <td class="px-6 py-4 whitespace-nowrap">${record.employee_name || 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap">${checkinTime}</td>
                <td class="px-6 py-4 whitespace-nowrap">${checkoutTime}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
                        ${label}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${calculateWorkHours(record.checkin_time, record.checkout_time)}
                </td>
            </tr>
        `;
    }).join('');
}

// Tính giờ làm việc
function calculateWorkHours(checkinTime, checkoutTime) {
    if (!checkinTime) return '';
    if (!checkoutTime) return '';

    const [hIn, mIn] = checkinTime.split(':').map(Number);
    const [hOut, mOut] = checkoutTime.split(':').map(Number);

    const start = new Date();
    start.setHours(hIn, mIn, 0, 0);
    const end = new Date();
    end.setHours(hOut, mOut, 0, 0);

    const diffMs = end - start;
    if (diffMs <= 0) return '';

    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs / (1000 * 60)) % 60);

    return `${hours}h ${minutes}m`;
}

// Format ngày hiển thị
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('vi-VN');
}

// Format ngày giờ chi tiết
function formatDateTime(dateTimeString) {
    return new Date(dateTimeString).toLocaleString('vi-VN');
}

// Xuất báo cáo Excel
async function exportAttendanceReport() {
    try {
        const dateFilter = document.getElementById('dateFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;

        let url = `${API_BASE_URL}/attendance/export`;
        const params = new URLSearchParams();

        if (dateFilter) params.append('date', dateFilter);
        if (statusFilter) params.append('status', statusFilter);

        if (params.toString()) {
            url += '?' + params.toString();
        }

        const response = await fetch(url, {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_report_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showNotification('Xuất báo cáo thành công!', 'success');
        } else {
            throw new Error('Không thể xuất báo cáo');
        }
    } catch (error) {
        console.error('Export report error:', error);
        showNotification('Lỗi khi xuất báo cáo', 'error');
    }
}

// Thiết lập bộ lọc
function setupAttendanceFilters() {
    const dateFilter = document.getElementById('dateFilter');
    const statusFilter = document.getElementById('statusFilter');

    // Set ngày mặc định là hôm nay
    dateFilter.value = formatDateForInput(new Date());

    dateFilter.addEventListener('change', loadAttendance);
    statusFilter.addEventListener('change', loadAttendance);
}

// Format ngày để gán cho input[type=date]
function formatDateForInput(date) {
    return date.toISOString().split('T')[0];
}

// Hiển thị chi tiết chấm công
function showAttendanceDetail(employeeCode, date) {
    const records = attendanceData.filter(record =>
        record.employee_code === employeeCode &&
        record.check_time.split('T')[0] === date
    );

    if (records.length === 0) return;

    let detailHtml = `
        <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4">
                <div class="p-6 border-b">
                    <h3 class="text-xl font-semibold text-gray-800">Chi tiết chấm công</h3>
                    <p class="text-gray-600">${records[0].employee_name || employeeCode} - ${formatDate(date)}</p>
                </div>
                <div class="p-6">
                    <div class="space-y-4">
    `;

    records.forEach(record => {
        const { label, class: statusClass } = mapStatus(record.work_status);
        detailHtml += `
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                    <p class="font-medium">${record.check_type === 'checkin' ? 'Vào làm' : 'Tan làm'}</p>
                    <p class="text-sm text-gray-600">${formatDateTime(record.check_time)}</p>
                </div>
                <span class="px-2 py-1 rounded-full text-xs font-medium ${statusClass}">
                    ${label}
                </span>
            </div>
        `;
    });

    detailHtml += `
                    </div>
                </div>
                <div class="p-6 border-t">
                    <button onclick="closeAttendanceDetail()" class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition duration-300">
                        Đóng
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', detailHtml);
}

// Đóng chi tiết chấm công
function closeAttendanceDetail() {
    const modal = document.querySelector('.fixed.inset-0.bg-black.bg-opacity-50');
    if (modal) {
        modal.remove();
    }
}

// Khởi tạo khi DOM loaded
document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('attendancePage')) {
        setupAttendanceFilters();
        loadAttendance();
    }
});

// Export functions
window.exportAttendanceReport = exportAttendanceReport;
window.showAttendanceDetail = showAttendanceDetail;
window.closeAttendanceDetail = closeAttendanceDetail;
