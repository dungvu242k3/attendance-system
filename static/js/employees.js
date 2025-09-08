// employees.js - Quản lý nhân viên
let employeesData = [];
let editingEmployeeId = null;

// Load danh sách nhân viên
async function loadEmployees() {
    try {
        const response = await fetch(`${API_BASE_URL}/employees`, {
            headers: getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (data.success) {
            employeesData = data.data;
            renderEmployeesTable(employeesData);
            setupEmployeeFilters();
        } else {
            showNotification(data.message || 'Không thể tải danh sách nhân viên', 'error');
        }
    } catch (error) {
        console.error('Load employees error:', error);
        showNotification('Lỗi khi tải danh sách nhân viên', 'error');
    }
}

// Render bảng nhân viên
function renderEmployeesTable(employees) {
    const tbody = document.getElementById('employeeTableBody');
    
    if (!employees || employees.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center text-gray-500">
                    Chưa có nhân viên nào
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = employees.map(employee => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                    <i class="fas fa-user text-gray-500"></i>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">${employee.employee_code}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">${employee.name}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">${employee.phone || ''}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">${employee.email || ''}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    ${employee.position || 'Nhân viên'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="editEmployee(${employee.id})" class="text-indigo-600 hover:text-indigo-900 mr-4">
                    <i class="fas fa-edit"></i> Sửa
                </button>
                <button onclick="deleteEmployee(${employee.id})" class="text-red-600 hover:text-red-900">
                    <i class="fas fa-trash"></i> Xóa
                </button>
            </td>
        </tr>
    `).join('');
}

// Thiết lập bộ lọc nhân viên
function setupEmployeeFilters() {
    const searchInput = document.getElementById('searchEmployee');
    const positionFilter = document.getElementById('filterPosition');
    
    // Tìm kiếm
    searchInput.addEventListener('input', function() {
        filterEmployees();
    });
    
    // Lọc theo chức vụ
    positionFilter.addEventListener('change', function() {
        filterEmployees();
    });
}

// Lọc nhân viên
function filterEmployees() {
    const searchTerm = document.getElementById('searchEmployee').value.toLowerCase();
    const selectedPosition = document.getElementById('filterPosition').value;
    
    let filtered = employeesData.filter(employee => {
        const matchSearch = !searchTerm || 
            employee.employee_code.toLowerCase().includes(searchTerm) ||
            employee.name.toLowerCase().includes(searchTerm);
            
        const matchPosition = !selectedPosition || 
            employee.position === selectedPosition;
            
        return matchSearch && matchPosition;
    });
    
    renderEmployeesTable(filtered);
}

// Thêm nhân viên mới
document.getElementById('addEmployeeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('employee_code', document.getElementById('employeeId').value);
    formData.append('name', document.getElementById('employeeName').value);
    formData.append('phone', document.getElementById('employeePhone').value);
    formData.append('email', document.getElementById('employeeEmail').value);
    formData.append('position', document.getElementById('employeePosition').value);
    
    const imageFile = document.getElementById('employeeImage').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/employees`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Thêm nhân viên thành công!', 'success');
            resetForm();
            loadEmployees(); // Reload danh sách
        } else {
            showNotification(data.message || 'Không thể thêm nhân viên', 'error');
        }
    } catch (error) {
        console.error('Add employee error:', error);
        showNotification('Lỗi khi thêm nhân viên', 'error');
    }
});

// Reset form thêm nhân viên
function resetForm() {
    document.getElementById('addEmployeeForm').reset();
    document.getElementById('imagePreview').innerHTML = '<i class="fas fa-camera text-gray-400 text-2xl"></i>';
}

// Preview ảnh khi chọn file
document.getElementById('employeeImage').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('imagePreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" class="w-full h-full object-cover rounded-full">`;
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '<i class="fas fa-camera text-gray-400 text-2xl"></i>';
    }
});

// Sửa nhân viên
function editEmployee(employeeId) {
    const employee = employeesData.find(emp => emp.id === employeeId);
    if (!employee) return;
    
    editingEmployeeId = employeeId;
    
    // Điền thông tin vào form edit
    document.getElementById('editEmployeePhone').value = employee.phone || '';
    document.getElementById('editEmployeeEmail').value = employee.email || '';
    document.getElementById('editEmployeePosition').value = employee.position || '';
    
    // Hiển thị modal
    document.getElementById('editModal').classList.remove('hidden');
    document.getElementById('editModal').classList.add('flex');
}

// Đóng modal edit
function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
    document.getElementById('editModal').classList.remove('flex');
    editingEmployeeId = null;
}

// Xử lý form edit nhân viên
document.getElementById('editEmployeeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!editingEmployeeId) return;
    
    const updateData = {
        email: document.getElementById('editEmployeeEmail').value,
        phone: document.getElementById('editEmployeePhone').value,
        position: document.getElementById('editEmployeePosition').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/employees/${editingEmployeeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Cập nhật nhân viên thành công!', 'success');
            closeEditModal();
            loadEmployees(); // Reload danh sách
        } else {
            showNotification(data.message || 'Không thể cập nhật nhân viên', 'error');
        }
    } catch (error) {
        console.error('Update employee error:', error);
        showNotification('Lỗi khi cập nhật nhân viên', 'error');
    }
});

// Xóa nhân viên
async function deleteEmployee(employeeId) {
    if (!confirm('Bạn có chắc chắn muốn xóa nhân viên này?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/employees/${employeeId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Xóa nhân viên thành công!', 'success');
            loadEmployees(); // Reload danh sách
        } else {
            showNotification(data.message || 'Không thể xóa nhân viên', 'error');
        }
    } catch (error) {
        console.error('Delete employee error:', error);
        showNotification('Lỗi khi xóa nhân viên', 'error');
    }
}

// Preview ảnh edit
document.getElementById('editEmployeeImage').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('editImagePreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" class="w-full h-full object-cover rounded-full">`;
        };
        reader.readAsDataURL(file);
    }
});

// Đóng modal khi click bên ngoài
document.getElementById('editModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeEditModal();
    }
});

// Export functions
window.editEmployee = editEmployee;
window.deleteEmployee = deleteEmployee;
window.closeEditModal = closeEditModal;
window.resetForm = resetForm;