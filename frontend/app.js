/**
 * Zalo OA Finance Workflow - Frontend Application
 * Full client-side logic for dashboard
 */

// Global State
const AppState = {
    token: localStorage.getItem('token') || null,
    user: null,
    currentPage: 'dashboard',
    leads: [],
    documents: [],
    users: [],
    socket: null,
    chatUserId: 'test_user_' + Math.random().toString(36).substr(2, 9),
    chatStartTime: new Date(),
    messageCount: 1
};

// API Base URL
const API_URL = window.location.origin + '/api';

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    if (AppState.token) {
        verifyToken();
    } else {
        showLoginScreen();
    }
    
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    // Login Form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            navigateTo(page);
        });
    });
    
    // Mobile Menu
    document.getElementById('mobile-menu-btn').addEventListener('click', toggleMobileMenu);
    
    // Chat
    document.getElementById('send-chat-btn').addEventListener('click', sendChatMessage);
    document.getElementById('chat-input-text').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
    
    // Quick Messages
    document.querySelectorAll('.quick-msg-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const msg = btn.getAttribute('data-msg');
            document.getElementById('chat-input-text').value = msg;
            sendChatMessage();
        });
    });
    
    // Modal Close on Overlay Click
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'modal-overlay') {
            closeModal();
        }
    });
    
    // Lead Search
    document.getElementById('lead-search').addEventListener('input', (e) => {
        filterLeads(e.target.value);
    });
}

// API Helper
async function apiCall(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (AppState.token) {
        headers['Authorization'] = `Bearer ${AppState.token}`;
    }
    
    const options = {
        method,
        headers
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API Error');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Auth Functions
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const result = await apiCall('/auth/login', 'POST', { username, password });
        
        AppState.token = result.token;
        AppState.user = result.user;
        
        localStorage.setItem('token', result.token);
        
        showToast('Đăng nhập thành công!', 'success');
        showDashboard();
        connectSocket();
        loadDashboardData();
    } catch (error) {
        showToast(error.message || 'Đăng nhập thất bại', 'error');
    }
}

async function verifyToken() {
    try {
        const user = await apiCall('/auth/me');
        AppState.user = user;
        showDashboard();
        connectSocket();
        loadDashboardData();
    } catch (error) {
        localStorage.removeItem('token');
        AppState.token = null;
        showLoginScreen();
    }
}

function handleLogout() {
    localStorage.removeItem('token');
    AppState.token = null;
    AppState.user = null;
    
    if (AppState.socket) {
        AppState.socket.disconnect();
    }
    
    showLoginScreen();
    showToast('Đã đăng xuất', 'success');
}

// UI Functions
function showLoginScreen() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
}

function showDashboard() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'flex';
    
    // Update user info
    if (AppState.user) {
        document.getElementById('user-name').textContent = AppState.user.name;
        document.getElementById('user-role').textContent = getRoleName(AppState.user.role);
    }
}

function getRoleName(roleKey) {
    const roleNames = {
        'quan_tri_vien': 'Quản trị viên',
        'soan_noi_dung': 'Soạn nội dung',
        'cskh': 'CSKH',
        'phan_tich_vien': 'Phân tích viên',
        'chuyen_vien_tu_van': 'Chuyên viên tư vấn'
    };
    return roleNames[roleKey] || roleKey;
}

function navigateTo(page) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-page') === page) {
            item.classList.add('active');
        }
    });
    
    // Update page
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`page-${page}`).classList.add('active');
    
    // Update title
    const titles = {
        'dashboard': 'Dashboard',
        'leads': 'Quản lý Lead',
        'chat': 'Chat Simulator',
        'documents': 'Hồ sơ số',
        'notifications': 'Thông báo',
        'users': 'Phân quyền',
        'reports': 'Báo cáo'
    };
    document.getElementById('page-title').textContent = titles[page] || page;
    
    AppState.currentPage = page;
    
    // Load page specific data
    switch (page) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'leads':
            loadLeads();
            break;
        case 'documents':
            loadDocuments();
            break;
        case 'notifications':
            loadNotificationTemplates();
            break;
        case 'users':
            loadUsers();
            break;
    }
    
    // Close mobile menu
    document.querySelector('.sidebar').classList.remove('open');
}

function toggleMobileMenu() {
    document.querySelector('.sidebar').classList.toggle('open');
}

// Dashboard Data
async function loadDashboardData() {
    try {
        const analytics = await apiCall('/analytics/dashboard');
        
        // Update stats
        document.getElementById('stat-total-leads').textContent = analytics.stats.total_leads;
        document.getElementById('stat-new-today').textContent = analytics.stats.new_leads_today;
        document.getElementById('stat-messages').textContent = analytics.stats.messages_sent;
        document.getElementById('stat-documents').textContent = analytics.stats.documents_processed;
        document.getElementById('stat-pending-docs').textContent = analytics.stats.pending_documents;
        document.getElementById('stat-conversion').textContent = analytics.conversion_rate + '%';
        
        // Update status chart
        const total = analytics.stats.total_leads || 1;
        const statusMap = analytics.lead_by_status || {};
        
        const statuses = ['tiep_nhan', 'dang_xu_ly', 'cho_bo_sung', 'hoan_thanh'];
        statuses.forEach(status => {
            const count = statusMap[status] || 0;
            const percentage = (count / total) * 100;
            
            const barId = 'bar-' + status.replace(/_/g, '-');
            const countId = 'count-' + status.replace(/_/g, '-');
            
            const barEl = document.getElementById(barId);
            const countEl = document.getElementById(countId);
            
            if (barEl) barEl.style.width = percentage + '%';
            if (countEl) countEl.textContent = count;
        });
        
        // Update recent leads
        renderRecentLeads(analytics.recent_leads || []);
        
        // Update notification count
        document.getElementById('notification-count').textContent = analytics.stats.new_leads_today;
        
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

function renderRecentLeads(leads) {
    const container = document.getElementById('recent-leads-list');
    
    if (leads.length === 0) {
        container.innerHTML = '<p class="empty-state">Chưa có lead nào</p>';
        return;
    }
    
    container.innerHTML = leads.map(lead => `
        <div class="lead-item">
            <div class="lead-info">
                <div class="lead-name">${lead.name || 'N/A'}</div>
                <div class="lead-product">${lead.product_interest || 'Chưa xác định'}</div>
            </div>
            <span class="lead-status ${lead.status}">${getStatusName(lead.status)}</span>
        </div>
    `).join('');
}

function getStatusName(status) {
    const statusNames = {
        'tiep_nhan': 'Tiếp nhận',
        'dang_xu_ly': 'Đang xử lý',
        'cho_bo_sung': 'Chờ bổ sung',
        'hoan_thanh': 'Hoàn thành'
    };
    return statusNames[status] || status;
}

// Leads Management
async function loadLeads() {
    try {
        const leads = await apiCall('/leads');
        AppState.leads = leads;
        renderLeadsTable(leads);
    } catch (error) {
        console.error('Failed to load leads:', error);
    }
}

function renderLeadsTable(leads) {
    const tbody = document.getElementById('leads-table-body');
    
    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Chưa có lead nào</td></tr>';
        return;
    }
    
    tbody.innerHTML = leads.map(lead => `
        <tr>
            <td><strong>${lead.id}</strong></td>
            <td>${lead.name}</td>
            <td>${lead.phone}</td>
            <td>${lead.product_interest || 'N/A'}</td>
            <td><span class="lead-status ${lead.status}">${getStatusName(lead.status)}</span></td>
            <td>${lead.assigned_to || 'Chưa phân công'}</td>
            <td>${formatDate(lead.created_at)}</td>
            <td>
                <button class="action-btn" onclick="editLead('${lead.id}')" title="Sửa">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                </button>
                <button class="action-btn" onclick="viewWorkflow('${lead.id}')" title="Workflow">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                    </svg>
                </button>
                <button class="action-btn delete" onclick="deleteLead('${lead.id}')" title="Xóa">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
}

function filterLeads(searchTerm) {
    const filtered = AppState.leads.filter(lead => 
        lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.phone.includes(searchTerm) ||
        lead.id.includes(searchTerm)
    );
    renderLeadsTable(filtered);
}

function showCreateLeadModal() {
    const modalContent = `
        <div class="modal-header">
            <h3>Tạo Lead mới</h3>
            <button class="modal-close" onclick="closeModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
        <div class="modal-body">
            <form id="create-lead-form">
                <div class="form-group">
                    <label>Họ tên *</label>
                    <input type="text" id="lead-name" required>
                </div>
                <div class="form-group">
                    <label>Số điện thoại *</label>
                    <input type="tel" id="lead-phone" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="lead-email">
                </div>
                <div class="form-group">
                    <label>Sản phẩm quan tâm</label>
                    <select id="lead-product">
                        <option value="">-- Chọn --</option>
                        <option value="vay_tieu_dung">Vay tiêu dùng</option>
                        <option value="bao_hiem">Bảo hiểm</option>
                        <option value="dau_tu">Đầu tư</option>
                        <option value="tiet_kiem">Tiết kiệm</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Ghi chú</label>
                    <textarea id="lead-notes" rows="3"></textarea>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal()">Hủy</button>
            <button class="btn-primary" onclick="createLead()">Tạo Lead</button>
        </div>
    `;
    
    document.getElementById('modal-content').innerHTML = modalContent;
    document.getElementById('modal-overlay').style.display = 'flex';
}

async function createLead() {
    const data = {
        name: document.getElementById('lead-name').value,
        phone: document.getElementById('lead-phone').value,
        email: document.getElementById('lead-email').value,
        product_interest: document.getElementById('lead-product').value,
        notes: document.getElementById('lead-notes').value
    };
    
    try {
        await apiCall('/leads', 'POST', data);
        closeModal();
        showToast('Tạo lead thành công!', 'success');
        loadLeads();
        loadDashboardData();
    } catch (error) {
        showToast('Tạo lead thất bại: ' + error.message, 'error');
    }
}

async function editLead(leadId) {
    const lead = AppState.leads.find(l => l.id === leadId);
    if (!lead) return;
    
    const modalContent = `
        <div class="modal-header">
            <h3>Chỉnh sửa Lead #${leadId}</h3>
            <button class="modal-close" onclick="closeModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
        <div class="modal-body">
            <form id="edit-lead-form">
                <div class="form-group">
                    <label>Họ tên</label>
                    <input type="text" id="edit-lead-name" value="${lead.name}">
                </div>
                <div class="form-group">
                    <label>Số điện thoại</label>
                    <input type="tel" id="edit-lead-phone" value="${lead.phone}">
                </div>
                <div class="form-group">
                    <label>Trạng thái</label>
                    <select id="edit-lead-status">
                        <option value="tiep_nhan" ${lead.status === 'tiep_nhan' ? 'selected' : ''}>Tiếp nhận</option>
                        <option value="dang_xu_ly" ${lead.status === 'dang_xu_ly' ? 'selected' : ''}>Đang xử lý</option>
                        <option value="cho_bo_sung" ${lead.status === 'cho_bo_sung' ? 'selected' : ''}>Chờ bổ sung</option>
                        <option value="hoan_thanh" ${lead.status === 'hoan_thanh' ? 'selected' : ''}>Hoàn thành</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Phân công cho</label>
                    <input type="text" id="edit-lead-assigned" value="${lead.assigned_to || ''}">
                </div>
                <div class="form-group">
                    <label>Ghi chú</label>
                    <textarea id="edit-lead-notes" rows="3">${lead.notes || ''}</textarea>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal()">Hủy</button>
            <button class="btn-primary" onclick="updateLead('${leadId}')">Cập nhật</button>
        </div>
    `;
    
    document.getElementById('modal-content').innerHTML = modalContent;
    document.getElementById('modal-overlay').style.display = 'flex';
}

async function updateLead(leadId) {
    const data = {
        name: document.getElementById('edit-lead-name').value,
        phone: document.getElementById('edit-lead-phone').value,
        status: document.getElementById('edit-lead-status').value,
        assigned_to: document.getElementById('edit-lead-assigned').value,
        notes: document.getElementById('edit-lead-notes').value
    };
    
    try {
        await apiCall(`/leads/${leadId}`, 'PUT', data);
        closeModal();
        showToast('Cập nhật lead thành công!', 'success');
        loadLeads();
        loadDashboardData();
    } catch (error) {
        showToast('Cập nhật thất bại: ' + error.message, 'error');
    }
}

async function deleteLead(leadId) {
    if (!confirm('Bạn có chắc muốn xóa lead này?')) return;
    
    try {
        await apiCall(`/leads/${leadId}`, 'DELETE');
        showToast('Đã xóa lead', 'success');
        loadLeads();
        loadDashboardData();
    } catch (error) {
        showToast('Xóa thất bại: ' + error.message, 'error');
    }
}

async function viewWorkflow(leadId) {
    try {
        const workflow = await apiCall(`/workflow/${leadId}/status`);
        
        const stepsHtml = workflow.steps.map(step => `
            <div class="workflow-step ${step.status}">
                <div class="step-icon">
                    ${step.status === 'completed' ? '✓' : '○'}
                </div>
                <div class="step-info">
                    <strong>${getStepName(step.step)}</strong>
                    <span>${step.timestamp ? formatDate(step.timestamp) : 'Chưa thực hiện'}</span>
                </div>
            </div>
        `).join('');
        
        const modalContent = `
            <div class="modal-header">
                <h3>Workflow Lead #${leadId}</h3>
                <button class="modal-close" onclick="closeModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <div class="workflow-timeline">
                    ${stepsHtml}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="closeModal()">Đóng</button>
            </div>
        `;
        
        document.getElementById('modal-content').innerHTML = modalContent;
        document.getElementById('modal-overlay').style.display = 'flex';
        
    } catch (error) {
        showToast('Không thể tải workflow', 'error');
    }
}

function getStepName(step) {
    const names = {
        'tiep_nhan': 'Tiếp nhận',
        'phan_loai': 'Phân loại',
        'tu_van': 'Tư vấn',
        'xu_ly_ho_so': 'Xử lý hồ sơ',
        'phe_duyet': 'Phê duyệt',
        'hoan_thanh': 'Hoàn thành'
    };
    return names[step] || step;
}

// Documents Management
async function loadDocuments() {
    try {
        const docs = await apiCall('/documents');
        AppState.documents = docs;
        renderDocumentsTable(docs);
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

function renderDocumentsTable(docs) {
    const tbody = document.getElementById('documents-table-body');
    
    if (docs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Chưa có hồ sơ nào</td></tr>';
        return;
    }
    
    tbody.innerHTML = docs.map(doc => `
        <tr>
            <td><strong>${doc.id}</strong></td>
            <td>${getDocTypeName(doc.type)}</td>
            <td>${doc.lead_id || 'N/A'}</td>
            <td>${doc.filename || 'N/A'}</td>
            <td><span class="lead-status ${doc.status}">${getDocStatusName(doc.status)}</span></td>
            <td>
                ${doc.ocr_data && Object.keys(doc.ocr_data).length > 0 ? `
                    <div class="ocr-data">
                        ${Object.entries(doc.ocr_data).slice(0, 3).map(([k, v]) => `<p><strong>${k}:</strong> ${v}</p>`).join('')}
                    </div>
                ` : 'Chưa xử lý'}
            </td>
            <td>${formatDate(doc.created_at)}</td>
            <td>
                <button class="action-btn" onclick="processOCR('${doc.id}')" title="OCR">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
}

function getDocTypeName(type) {
    const names = {
        'cccd': 'CCCD',
        'dkkd': 'ĐKKD',
        'thue': 'Thuế',
        'hop_dong': 'Hợp đồng',
        'khac': 'Khác'
    };
    return names[type] || type;
}

function getDocStatusName(status) {
    const names = {
        'pending': 'Chờ xử lý',
        'processing': 'Đang xử lý',
        'verified': 'Đã xác minh',
        'rejected': 'Từ chối'
    };
    return names[status] || status;
}

function showUploadDocModal() {
    const modalContent = `
        <div class="modal-header">
            <h3>Upload Hồ sơ</h3>
            <button class="modal-close" onclick="closeModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
        <div class="modal-body">
            <form id="upload-doc-form">
                <div class="form-group">
                    <label>Loại hồ sơ *</label>
                    <select id="doc-type" required>
                        <option value="cccd">CCCD</option>
                        <option value="dkkd">Đăng ký kinh doanh</option>
                        <option value="thue">Thuế</option>
                        <option value="hop_dong">Hợp đồng</option>
                        <option value="khac">Khác</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Lead ID</label>
                    <input type="text" id="doc-lead-id" placeholder="VD: abc123">
                </div>
                <div class="form-group">
                    <label>Tên file</label>
                    <input type="text" id="doc-filename" value="document_demo.pdf">
                </div>
                <div class="form-group">
                    <label>Ghi chú</label>
                    <textarea id="doc-notes" rows="3"></textarea>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal()">Hủy</button>
            <button class="btn-primary" onclick="uploadDocument()">Upload</button>
        </div>
    `;
    
    document.getElementById('modal-content').innerHTML = modalContent;
    document.getElementById('modal-overlay').style.display = 'flex';
}

async function uploadDocument() {
    const data = {
        type: document.getElementById('doc-type').value,
        lead_id: document.getElementById('doc-lead-id').value,
        filename: document.getElementById('doc-filename').value,
        file_size: Math.floor(Math.random() * 1000000),
        notes: document.getElementById('doc-notes').value
    };
    
    try {
        await apiCall('/documents', 'POST', data);
        closeModal();
        showToast('Upload hồ sơ thành công!', 'success');
        loadDocuments();
        loadDashboardData();
    } catch (error) {
        showToast('Upload thất bại: ' + error.message, 'error');
    }
}

async function processOCR(docId) {
    try {
        await apiCall(`/documents/${docId}/ocr`, 'POST');
        showToast('Xử lý OCR thành công!', 'success');
        loadDocuments();
    } catch (error) {
        showToast('OCR thất bại: ' + error.message, 'error');
    }
}

// Notifications
async function loadNotificationTemplates() {
    try {
        const templates = await apiCall('/notifications/templates');
        renderNotificationTemplates(templates);
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

function renderNotificationTemplates(templates) {
    const container = document.getElementById('notification-templates');
    
    container.innerHTML = Object.entries(templates).map(([key, template]) => `
        <div class="template-card">
            <h4>${template.name}</h4>
            <p>${template.content}</p>
            <div class="template-channels">
                ${template.channels.map(ch => `<span class="channel-tag">${ch}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

// Users Management
async function loadUsers() {
    try {
        const users = await apiCall('/users');
        AppState.users = users;
        renderUsersTable(users);
    } catch (error) {
        console.error('Failed to load users:', error);
        document.getElementById('users-table-body').innerHTML = 
            '<tr><td colspan="6" class="empty-state">Không có quyền xem danh sách users</td></tr>';
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td><strong>${user.username}</strong></td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td><span class="role-badge">${getRoleName(user.role)}</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <button class="action-btn" onclick="editUser('${user.id}')" title="Sửa">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
}

function showCreateUserModal() {
    const modalContent = `
        <div class="modal-header">
            <h3>Thêm User mới</h3>
            <button class="modal-close" onclick="closeModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
        <div class="modal-body">
            <form id="create-user-form">
                <div class="form-group">
                    <label>Username *</label>
                    <input type="text" id="new-username" required>
                </div>
                <div class="form-group">
                    <label>Mật khẩu *</label>
                    <input type="password" id="new-password" value="123456">
                </div>
                <div class="form-group">
                    <label>Họ tên *</label>
                    <input type="text" id="new-name" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="new-email">
                </div>
                <div class="form-group">
                    <label>Vai trò</label>
                    <select id="new-role">
                        <option value="cskh">CSKH</option>
                        <option value="soan_noi_dung">Soạn nội dung</option>
                        <option value="chuyen_vien_tu_van">Chuyên viên tư vấn</option>
                        <option value="phan_tich_vien">Phân tích viên</option>
                        <option value="quan_tri_vien">Quản trị viên</option>
                    </select>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal()">Hủy</button>
            <button class="btn-primary" onclick="createUser()">Tạo User</button>
        </div>
    `;
    
    document.getElementById('modal-content').innerHTML = modalContent;
    document.getElementById('modal-overlay').style.display = 'flex';
}

async function createUser() {
    const data = {
        username: document.getElementById('new-username').value,
        password: document.getElementById('new-password').value,
        name: document.getElementById('new-name').value,
        email: document.getElementById('new-email').value,
        role: document.getElementById('new-role').value
    };
    
    try {
        await apiCall('/auth/register', 'POST', data);
        closeModal();
        showToast('Tạo user thành công!', 'success');
        loadUsers();
    } catch (error) {
        showToast('Tạo user thất bại: ' + error.message, 'error');
    }
}

// Reports
async function exportReport() {
    try {
        const report = await apiCall('/analytics/reports?type=summary');
        
        const reportContent = `
=== BÁO CÁO TỔNG HỢP ===
Thời gian: ${formatDate(report.generated_at)}

--- THỐNG KÊ ---
• Tổng số Lead: ${report.data.total_leads}
• Tổng hội thoại: ${report.data.total_conversations}
• Tổng hồ sơ: ${report.data.total_documents}
• Tổng thông báo: ${report.data.total_notifications}
• Số users: ${report.data.users}

--- KẾT THÚC BÁO CÁO ---
        `;
        
        document.getElementById('report-summary').textContent = reportContent;
        showToast('Đã xuất báo cáo', 'success');
    } catch (error) {
        showToast('Xuất báo cáo thất bại', 'error');
    }
}

// Chat Simulator
function sendChatMessage() {
    const input = document.getElementById('chat-input-text');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';
    
    // Update message count
    AppState.messageCount++;
    document.getElementById('chat-message-count').textContent = AppState.messageCount;
    
    // Send to backend
    if (AppState.socket && AppState.socket.connected) {
        AppState.socket.emit('chat_message', {
            user_id: AppState.chatUserId,
            message: message
        });
    } else {
        // Fallback: simulate local response
        setTimeout(() => {
            const response = simulateLocalChatResponse(message);
            addChatMessage('bot', response);
            AppState.messageCount++;
            document.getElementById('chat-message-count').textContent = AppState.messageCount;
        }, 500);
    }
}

function addChatMessage(sender, text) {
    const container = document.getElementById('chat-messages');
    const time = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    
    const messageHtml = `
        <div class="message ${sender}">
            <div class="message-content">${text}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', messageHtml);
    container.scrollTop = container.scrollHeight;
}

function simulateLocalChatResponse(message) {
    const messageLower = message.toLowerCase();
    
    if (messageLower.includes('chào') || messageLower.includes('hello')) {
        return 'Xin chào! Tôi là trợ lý tư vấn tài chính. Tôi có thể giúp gì cho bạn?';
    }
    
    if (messageLower.includes('đăng ký') || messageLower.includes('tư vấn')) {
        return 'Để đăng ký tư vấn, vui lòng cung cấp:\n1. Họ tên\n2. Số điện thoại\n3. Nhu cầu tài chính';
    }
    
    if (messageLower.includes('sản phẩm') || messageLower.includes('dịch vụ')) {
        return 'Chúng tôi cung cấp:\n✅ Vay tiêu dùng\n✅ Bảo hiểm nhân thọ\n✅ Đầu tư chứng khoán\n✅ Tiết kiệm lãi suất cao';
    }
    
    if (messageLower.includes('hồ sơ') || messageLower.includes('giấy tờ')) {
        return 'Hồ sơ cần thiết:\n📋 CCCD/CMND\n📋 Sổ hộ khẩu\n📋 Giấy xác nhận thu nhập\n📋 Hợp đồng lao động (nếu có)';
    }
    
    if (messageLower.includes('nhân viên') || messageLower.includes('người thật')) {
        return 'Tôi sẽ chuyển bạn đến chuyên viên tư vấn ngay. Vui lòng chờ trong giây lát...';
    }
    
    if (messageLower.includes('cảm ơn') || messageLower.includes('thank')) {
        return 'Cảm ơn bạn đã liên hệ! Chúc bạn một ngày tốt lành! 🌟';
    }
    
    return 'Cảm ơn bạn đã liên hệ. Bạn có thể:\n1. Đăng ký tư vấn\n2. Xem sản phẩm\n3. Hỏi về hồ sơ\n4. Gặp nhân viên';
}

function resetChat() {
    const container = document.getElementById('chat-messages');
    container.innerHTML = `
        <div class="message bot">
            <div class="message-content">
                Xin chào! Tôi là trợ lý tư vấn tài chính. Tôi có thể giúp gì cho bạn?
            </div>
            <div class="message-time">${new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
    `;
    
    AppState.chatUserId = 'test_user_' + Math.random().toString(36).substr(2, 9);
    AppState.chatStartTime = new Date();
    AppState.messageCount = 1;
    
    document.getElementById('chat-user-id').textContent = AppState.chatUserId;
    document.getElementById('chat-message-count').textContent = '1';
    document.getElementById('chat-duration').textContent = '00:00';
    
    showToast('Đã reset chat', 'success');
}

// Update chat duration
setInterval(() => {
    const elapsed = Math.floor((new Date() - AppState.chatStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const seconds = (elapsed % 60).toString().padStart(2, '0');
    document.getElementById('chat-duration').textContent = `${minutes}:${seconds}`;
}, 1000);

// Socket.IO Connection
function connectSocket() {
    try {
        AppState.socket = io('/dashboard');
        
        AppState.socket.on('connect', () => {
            console.log('Connected to dashboard socket');
        });
        
        AppState.socket.on('new_lead', (lead) => {
            showToast(`Lead mới: ${lead.name}`, 'success');
            if (AppState.currentPage === 'dashboard') {
                loadDashboardData();
            }
            if (AppState.currentPage === 'leads') {
                loadLeads();
            }
        });
        
        AppState.socket.on('lead_updated', (lead) => {
            if (AppState.currentPage === 'leads') {
                loadLeads();
            }
        });
        
        AppState.socket.on('bot_response', (data) => {
            addChatMessage('bot', data.response.text);
            AppState.messageCount++;
            document.getElementById('chat-message-count').textContent = AppState.messageCount;
        });
        
        AppState.socket.on('new_message', (data) => {
            const count = parseInt(document.getElementById('notification-count').textContent) + 1;
            document.getElementById('notification-count').textContent = count;
        });
        
    } catch (error) {
        console.warn('Socket connection failed, using fallback mode');
    }
}

// Utility Functions
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
            ${type === 'success' ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>' : 
              type === 'error' ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' :
              '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'}
        </svg>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 300ms ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Additional CSS for workflow timeline (inject dynamically)
const additionalStyles = document.createElement('style');
additionalStyles.textContent = `
    .workflow-timeline {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    
    .workflow-step {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px;
        background: var(--bg-page);
        border-radius: 8px;
    }
    
    .workflow-step.completed {
        background: var(--success-100);
    }
    
    .step-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--bg-surface);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: var(--text-secondary);
    }
    
    .workflow-step.completed .step-icon {
        background: var(--success);
        color: white;
    }
    
    .step-info {
        display: flex;
        flex-direction: column;
    }
    
    .step-info strong {
        font-size: 14px;
    }
    
    .step-info span {
        font-size: 12px;
        color: var(--text-secondary);
    }
`;
document.head.appendChild(additionalStyles);

// Make functions globally accessible
window.navigateTo = navigateTo;
window.showCreateLeadModal = showCreateLeadModal;
window.createLead = createLead;
window.editLead = editLead;
window.updateLead = updateLead;
window.deleteLead = deleteLead;
window.viewWorkflow = viewWorkflow;
window.showUploadDocModal = showUploadDocModal;
window.uploadDocument = uploadDocument;
window.processOCR = processOCR;
window.showCreateUserModal = showCreateUserModal;
window.createUser = createUser;
window.exportReport = exportReport;
window.resetChat = resetChat;
window.closeModal = closeModal;
