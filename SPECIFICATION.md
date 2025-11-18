# 🎯 ĐẶCẢ TẢ HỆ THỐNG TƯ VẤN VAY VỐN

> **Mục đích:** Chuyển đổi repo demo thành hệ thống môi giới vay vốn thực tế  
> **Mô hình:** Thu hồ sơ → Xử lý → Bàn giao ngân hàng → Nhận hoa hồng

---

## I. GAP ANALYSIS

### ✅ CODE HIỆN TẠI (45%)

| Thành phần | Trạng thái | Mô tả |
|------------|-----------|-------|
| UI Dashboard | ✅ Hoàn chỉnh | Giao diện đẹp, responsive |
| CRUD Leads | ✅ Hoàn chỉnh | Tạo/sửa/xóa/xem lead |
| Workflow | ✅ Logic có | 6 bước: Tiếp nhận → Phân loại → Tư vấn → Xử lý → Phê duyệt → Hoàn thành |
| Phân quyền cơ bản | ✅ Có | 5 vai trò: Admin, Soạn nội dung, CSKH, Phân tích viên, Chuyên viên tư vấn |
| Documents management | ✅ Structure | Upload, theo dõi trạng thái |
| Thông báo tự động | ✅ Có mẫu | 6 mẫu thông báo |
| Analytics | ✅ Hoàn chỉnh | Dashboard, báo cáo |

### ❌ CẦN BỔ SUNG (55%)

| Thành phần | Trạng thái | Mức độ ưu tiên |
|------------|-----------|----------------|
| Vai trò CTV/Cò | ❌ Chưa có | 🔴 CAO |
| Vai trò Sale ngân hàng | ❌ Chưa có | 🔴 CAO |
| Phân quyền theo phạm vi | ❌ Chưa có | 🔴 CAO |
| Zalo OA API thật | ❌ Giả lập | 🔴 CAO |
| OCR CCCD | ❌ Giả lập | 🔴 CAO |
| Check MST/thuế | ❌ Không có | 🔴 CAO |
| Tự động điền Word | ❌ Không có | 🔴 CAO |
| Database thật | ❌ RAM only | 🔴 CAO |
| Phân công tự động | ❌ Không có | 🟡 TB |
| Tính DTI/Rủi ro | ❌ Không có | 🟡 TB |

---

## II. KIẾN TRÚC MỚI

### 2.1. Kiến Trúc 2 Lớp

```
┌─────────────────────────────────────────────┐
│         ZALO OA KHÁCH HÀNG (Frontend)       │
│  - Chatbot AI thu thập thông tin            │
│  - Upload CCCD, giấy tờ                     │
│  - Nhận thông báo trạng thái                │
└─────────────────┬───────────────────────────┘
                  │ Webhook/API
                  ▼
┌─────────────────────────────────────────────┐
│            BACKEND (Repo này)               │
│  - Xử lý OCR, check MST                     │
│  - Điền form Word tự động                   │
│  - Phân công, workflow                      │
│  - Lưu trữ Google Sheets                    │
└─────────────────┬───────────────────────────┘
                  │ Notification API
                  ▼
┌─────────────────────────────────────────────┐
│         ZALO OA NỘI BỘ (Backend)            │
│  - Thông báo phân công cho nhân viên        │
│  - Giao hồ sơ cho sale ngân hàng            │
│  - Cập nhật trạng thái                      │
└─────────────────────────────────────────────┘
```

### 2.2. Vai Trò & Phân Quyền

```python
ROLES = {
    'admin': {
        'name': 'Admin (Chủ hệ thống)',
        'permissions': ['all'],
        'scope': 'all_leads'
    },
    'tro_ly': {
        'name': 'Trợ lý hệ thống',
        'permissions': ['view_all', 'assign', 'monitor', 'report'],
        'scope': 'all_leads'
    },
    'nhan_vien': {
        'name': 'Nhân viên xử lý hồ sơ',
        'permissions': ['view_assigned', 'update_status', 'upload_docs', 'fill_form'],
        'scope': 'assigned_leads_only'
    },
    'ctv': {
        'name': 'CTV/Cò',
        'permissions': ['create_lead', 'upload_cccd', 'view_own_leads'],
        'scope': 'own_leads_only'
    },
    'sale_ngan_hang': {
        'name': 'Sale Ngân hàng',
        'permissions': ['view_branch_leads', 'download_clean_docs', 'update_result'],
        'scope': 'branch_leads_only'
    }
}
```

### 2.3. Lead Model Mới

```python
lead = {
    'id': 'HS12345',
    'created_by': 'ctv_nguyen_van_a',  # CTV tạo
    'assigned_to': 'staff_001',         # Nhân viên được giao
    'source': 'ctv_nguyen_van_a',       # Nguồn lead
    'branch': 'vpbank_hcm_q1',          # Chi nhánh ngân hàng
    
    # Thông tin khách hàng
    'ho_ten': 'Nguyễn Văn A',
    'so_cccd': '001234567890',
    'ngay_sinh': '01/01/1990',
    'dia_chi': '123 Đường ABC, Q1, TP.HCM',
    'phone': '0901234567',
    
    # Thông tin DN (nếu có)
    'loai_hinh': 'ca_nhan',  # ca_nhan | ho_kinh_doanh | doanh_nghiep
    'mst': None,
    'ten_dn': None,
    
    # Thông tin vay
    'loai_vay': 'tin_chap',  # tin_chap | the_chap | sme
    'so_tien_vay': 100000000,
    'thoi_han': 12,
    'muc_dich_vay': 'Kinh doanh',
    'thu_nhap_thang': 20000000,
    
    # Đánh giá tự động
    'dti_ratio': 45.0,
    'risk_level': 'trung_binh',  # thap | trung_binh | cao
    'mst_status': None,
    
    # Workflow
    'status': 'tiep_nhan',  # tiep_nhan | dang_xu_ly | cho_bo_sung | hoan_thanh
    'workflow_steps': [...],
    
    # Files
    'cccd_front': 'url_to_image',
    'cccd_back': 'url_to_image',
    'documents': [...],
    'form_word_path': None,
    
    # Phân quyền xem
    'visibility': {
        'ctv': ['ctv_nguyen_van_a'],
        'staff': ['staff_001'],
        'bank': ['sale_vpbank_001'],
        'admin': True
    },
    
    'created_at': '2025-01-18T10:00:00',
    'updated_at': '2025-01-18T10:00:00'
}
```

---

## III. CHỨC NĂNG CẦN BỔ SUNG

### 3.1. Tích Hợp Zalo OA

**File:** `backend/integrations/zalo_oa.py`

```python
class ZaloOAClient:
    """Client kết nối Zalo OA thật"""
    
    def __init__(self, oa_id, access_token):
        self.oa_id = oa_id
        self.access_token = access_token
        self.api_url = "https://openapi.zalo.me/v2.0"
    
    def send_message(self, user_id, message):
        """Gửi tin nhắn cho user"""
        pass
    
    def upload_image(self, image_path):
        """Upload ảnh lên Zalo"""
        pass
    
    def send_notification(self, user_id, template, params):
        """Gửi thông báo theo template"""
        pass
```

**API endpoints cần thêm:**
- `POST /api/zalo/webhook` - Nhận sự kiện từ Zalo (đã có, cần sửa)
- `POST /api/zalo/send-to-customer` - Gửi tin cho khách
- `POST /api/zalo/send-to-staff` - Gửi tin cho nhân viên

### 3.2. OCR CCCD

**File:** `backend/services/ocr_service.py`

```python
class OCRService:
    """Dịch vụ OCR CCCD - dùng Google Vision API free tier"""
    
    def extract_cccd(self, image_path):
        """
        Đọc ảnh CCCD, trích xuất:
        - Số CCCD
        - Họ tên
        - Ngày sinh
        - Địa chỉ
        """
        return {
            'so_cccd': '001234567890',
            'ho_ten': 'NGUYỄN VĂN A',
            'ngay_sinh': '01/01/1990',
            'dia_chi': '123 Đường ABC...'
        }
```

**Thư viện dùng:**
- `google-cloud-vision` (free 1000 lượt/tháng)
- Hoặc `pytesseract` (free 100%, độ chính xác thấp hơn)

### 3.3. Check MST/Thuế

**File:** `backend/services/tax_service.py`

```python
class TaxService:
    """Kiểm tra MST qua API công khai"""
    
    def check_mst(self, mst):
        """
        Check tình trạng MST
        API: https://api.tracuuthue.vn/v1/mst/{mst}
        """
        return {
            'mst': mst,
            'ten_doanh_nghiep': 'CÔNG TY ABC',
            'tinh_trang': 'Hoạt động',  # Hoạt động | Ngừng | Giải thể
            'no_thue': 0,
            'nguoi_dai_dien': 'Nguyễn Văn A'
        }
    
    def extract_mst_from_cccd(self, cccd_number):
        """
        Logic: Lấy số CCCD → tìm MST liên kết
        (Cần API hoặc database mapping)
        """
        pass
```

### 3.4. Tự Động Điền Form Word

**File:** `backend/services/form_service.py`

```python
from docx import Document

class FormService:
    """Tự động điền form Word"""
    
    def fill_vpbank_form(self, lead_data, template_path):
        """
        Điền dữ liệu vào template Word
        Template có các placeholder: {{HO_TEN}}, {{CCCD}}, etc.
        """
        doc = Document(template_path)
        
        replacements = {
            '{{HO_TEN}}': lead_data['ho_ten'],
            '{{SO_CCCD}}': lead_data['so_cccd'],
            '{{DIA_CHI}}': lead_data['dia_chi'],
            # ... etc
        }
        
        # Replace trong paragraphs
        for paragraph in doc.paragraphs:
            for key, value in replacements.items():
                if key in paragraph.text:
                    paragraph.text = paragraph.text.replace(key, str(value))
        
        # Replace trong tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for key, value in replacements.items():
                        if key in cell.text:
                            cell.text = cell.text.replace(key, str(value))
        
        output_path = f'output/form_{lead_data["id"]}.docx'
        doc.save(output_path)
        return output_path
```

### 3.5. Tính DTI & Đánh Giá Rủi Ro

**File:** `backend/services/risk_service.py`

```python
class RiskAssessmentService:
    """Đánh giá rủi ro tự động"""
    
    def calculate_dti(self, so_tien_vay, thoi_han, thu_nhap_thang, lai_suat=0.15):
        """
        DTI = (Trả góp/tháng / Thu nhập) × 100%
        """
        monthly_payment = (so_tien_vay * lai_suat / 12) / \
                         (1 - (1 + lai_suat/12)**(-thoi_han))
        dti = (monthly_payment / thu_nhap_thang) * 100
        return round(dti, 2)
    
    def assess_risk(self, lead_data):
        """
        Đánh giá rủi ro tổng thể
        """
        dti = self.calculate_dti(
            lead_data['so_tien_vay'],
            lead_data['thoi_han'],
            lead_data['thu_nhap_thang']
        )
        
        risk_level = 'thap'
        reasons = []
        
        if dti > 50:
            risk_level = 'cao'
            reasons.append('DTI ratio quá cao (>50%)')
        elif dti > 35:
            risk_level = 'trung_binh'
            reasons.append('DTI ratio ở mức trung bình (35-50%)')
        
        if lead_data.get('mst_status') == 'Ngừng hoạt động':
            risk_level = 'cao'
            reasons.append('DN ngừng hoạt động')
        
        return {
            'dti_ratio': dti,
            'risk_level': risk_level,
            'reasons': reasons
        }
```

### 3.6. Phân Công Tự Động

**File:** `backend/services/assignment_service.py`

```python
class AssignmentService:
    """Phân công hồ sơ tự động"""
    
    def auto_assign(self, lead):
        """
        Quy tắc phân công:
        1. Theo khu vực
        2. Theo tải công việc
        3. Theo kỹ năng
        """
        # 1. Lọc theo khu vực
        region = self.detect_region(lead['dia_chi'])
        available_staff = self.get_staff_by_region(region)
        
        # 2. Chọn nhân viên ít việc nhất
        staff_workload = {}
        for staff in available_staff:
            workload = self.count_active_leads(staff['id'])
            staff_workload[staff['id']] = workload
        
        assigned_staff = min(staff_workload, key=staff_workload.get)
        
        return assigned_staff
```

### 3.7. Lưu Trữ Google Sheets

**File:** `backend/integrations/google_sheets.py`

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheetsClient:
    """Đồng bộ dữ liệu lên Google Sheets"""
    
    def __init__(self, credentials_path):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope
        )
        self.client = gspread.authorize(creds)
    
    def sync_lead(self, lead_data):
        """Đồng bộ lead lên Sheets"""
        sheet = self.client.open('CRM Vay Vốn').worksheet('Leads')
        
        row = [
            lead_data['id'],
            lead_data['ho_ten'],
            lead_data['so_cccd'],
            lead_data['phone'],
            lead_data['loai_vay'],
            lead_data['so_tien_vay'],
            lead_data['source'],
            lead_data['status'],
            lead_data['created_at']
        ]
        
        sheet.append_row(row)
```

---

## IV. DANH SÁCH FILE CẦN THÊM/SỬA

### Thêm mới:

```
backend/
├── integrations/
│   ├── __init__.py
│   ├── zalo_oa.py          # ✅ Tích hợp Zalo OA thật
│   └── google_sheets.py    # ✅ Đồng bộ Google Sheets
├── services/
│   ├── __init__.py
│   ├── ocr_service.py      # ✅ OCR CCCD
│   ├── tax_service.py      # ✅ Check MST/thuế
│   ├── form_service.py     # ✅ Điền form Word
│   ├── risk_service.py     # ✅ Đánh giá rủi ro
│   └── assignment_service.py # ✅ Phân công tự động
└── templates/
    └── vpbank_form.docx    # ✅ Template form Word
```

### Sửa đổi:

```
backend/
├── app.py                  # ⚠️ Sửa logic phân quyền, thêm vai trò mới
├── requirements.txt        # ⚠️ Thêm thư viện: gspread, python-docx, google-cloud-vision
└── config/
    └── .env.example        # ⚠️ Thêm biến môi trường Zalo OA, Google
```

---

## V. BIẾN MÔI TRƯỜNG CẦN THÊM

```bash
# .env

# Zalo OA Khách hàng
ZALO_OA_KHACH_ID=oa_khach_real_id
ZALO_OA_KHACH_ACCESS_TOKEN=real_access_token_khach

# Zalo OA Nội bộ
ZALO_OA_NOIBI_ID=oa_noibi_real_id
ZALO_OA_NOIBI_ACCESS_TOKEN=real_access_token_noibi

# Google Sheets
GOOGLE_CREDENTIALS_PATH=config/google_credentials.json
GOOGLE_SHEET_NAME=CRM Vay Vốn

# Google Vision OCR (optional)
GOOGLE_APPLICATION_CREDENTIALS=config/google_vision_credentials.json

# Cấu hình đánh giá rủi ro
DTI_LOW_THRESHOLD=35
DTI_HIGH_THRESHOLD=50
```

---

## VI. THƯ VIỆN CẦN THÊM

```txt
# requirements.txt (thêm vào)

# Zalo OA (dùng requests)
requests==2.31.0

# Google Sheets
gspread==5.12.4
oauth2client==4.1.3

# OCR
google-cloud-vision==3.5.0
# Hoặc dùng pytesseract (free)
pytesseract==0.3.10
Pillow==10.1.0

# Xử lý Word
python-docx==1.1.0

# Xử lý Excel (nếu cần)
openpyxl==3.1.2
```

---

## VII. WORKFLOW CHI TIẾT

### 7.1. Luồng Tiếp Nhận Lead

```
1. Khách gửi CCCD qua Zalo OA Khách
   ↓
2. Webhook gửi về backend
   ↓
3. OCRService.extract_cccd(image)
   ↓
4. TaxService.extract_mst_from_cccd(cccd_number)
   ↓
5. TaxService.check_mst(mst) [nếu là DN]
   ↓
6. Tạo Lead trong database
   ↓
7. AssignmentService.auto_assign(lead)
   ↓
8. ZaloOA.send_to_staff(assigned_staff, "Bạn có hồ sơ mới")
   ↓
9. GoogleSheets.sync_lead(lead)
   ↓
10. ZaloOA.send_to_customer(customer, "Đã nhận hồ sơ #HS12345")
```

### 7.2. Luồng Xử Lý Hồ Sơ

```
1. Nhân viên nhận thông báo trên Zalo OA Nội bộ
   ↓
2. Truy cập dashboard, xem chi tiết lead
   ↓
3. RiskService.assess_risk(lead) → hiển thị DTI, rủi ro
   ↓
4. FormService.fill_vpbank_form(lead, template) → tạo file Word
   ↓
5. Nhân viên review, chỉnh sửa (nếu cần)
   ↓
6. Upload file Word hoàn chỉnh
   ↓
7. Cập nhật status = "cho_phe_duyet"
   ↓
8. ZaloOA.send_to_bank_sale(sale_ngan_hang, "Hồ sơ #HS12345 đã sẵn sàng")
```

### 7.3. Luồng Bàn Giao Ngân Hàng

```
1. Sale ngân hàng nhận thông báo
   ↓
2. Truy cập dashboard với quyền sale_ngan_hang
   ↓
3. Chỉ thấy lead thuộc chi nhánh của mình
   ↓
4. Download file Word + tài liệu đã làm sạch
   ↓
5. Xử lý với ngân hàng
   ↓
6. Cập nhật kết quả: duyet | tu_choi | can_bo_sung
   ↓
7. System sync trạng thái về CRM
   ↓
8. ZaloOA.send_to_customer(customer, thông báo kết quả)
   ↓
9. ZaloOA.send_to_ctv(ctv, thông báo kết quả)
```

---

## VIII. API ENDPOINTS CẦN SỬA/THÊM

### Sửa đổi:

- `POST /api/auth/register` → Thêm vai trò ctv, sale_ngan_hang
- `GET /api/leads` → Filter theo scope (chỉ thấy lead được phép)
- `POST /api/leads` → Thêm logic gắn source, phân công tự động
- `POST /api/zalo/webhook` → Xử lý thật, không giả lập

### Thêm mới:

```python
# OCR & Processing
POST /api/ocr/cccd          # Upload ảnh CCCD → OCR
POST /api/tax/check-mst     # Check MST
POST /api/forms/fill        # Điền form Word tự động
POST /api/risk/assess       # Đánh giá rủi ro

# Assignment
POST /api/leads/{id}/assign      # Phân công thủ công
POST /api/leads/{id}/auto-assign # Phân công tự động

# Sync
POST /api/sync/google-sheets     # Đồng bộ lên Google Sheets

# Zalo OA
POST /api/zalo/send-to-customer  # Gửi tin cho khách
POST /api/zalo/send-to-staff     # Gửi tin cho nhân viên nội bộ
```

---

## IX. CHECKLIST TRIỂN KHAI

### Phase 1: Core (Tuần 1-2)

- [ ] Thêm vai trò ctv, sale_ngan_hang vào `ROLES`
- [ ] Sửa logic phân quyền `can_view_lead()`
- [ ] Thêm field `source`, `branch`, `visibility` vào Lead model
- [ ] Tạo `integrations/zalo_oa.py`
- [ ] Sửa `/api/zalo/webhook` xử lý thật
- [ ] Test gửi/nhận tin nhắn Zalo OA

### Phase 2: Processing (Tuần 3-4)

- [ ] Tạo `services/ocr_service.py`
- [ ] Tạo `services/tax_service.py`
- [ ] Tạo `services/form_service.py`
- [ ] Tạo `services/risk_service.py`
- [ ] Test OCR → Check MST → Điền form → Đánh giá rủi ro

### Phase 3: Automation (Tuần 5-6)

- [ ] Tạo `services/assignment_service.py`
- [ ] Tạo `integrations/google_sheets.py`
- [ ] Kết nối Google Sheets
- [ ] Test phân công tự động
- [ ] Test đồng bộ dữ liệu

### Phase 4: Integration (Tuần 7-8)

- [ ] Tích hợp toàn bộ luồng end-to-end
- [ ] Test với data thật
- [ ] Fix bugs
- [ ] Tối ưu performance
- [ ] Deploy lên VPS

---

## X. THÔNG TIN CẦN TỪ KHÁCH HÀNG

### 1. Tài liệu nghiệp vụ:
- [ ] Tài liệu chính sách sản phẩm vay
- [ ] File Word template form VPBank
- [ ] Bảng tính/công thức (nếu có)

### 2. Quy tắc nghiệp vụ:
- [ ] Ngưỡng DTI chấp nhận/từ chối
- [ ] Quy tắc phân công (khu vực, kỹ năng)
- [ ] SLA mong muốn (thời gian xử lý)

### 3. Danh sách nhân sự:
- [ ] Danh sách CTV (tên, số Zalo)
- [ ] Danh sách nhân viên nội bộ (tên, khu vực, kỹ năng)
- [ ] Danh sách sale ngân hàng (tên, chi nhánh, số Zalo)

### 4. Quyền truy cập:
- [ ] Quyền admin 2 Zalo OA
- [ ] Tài khoản Google (để setup Google Sheets)
- [ ] API credentials (sau khi đăng ký)

### 5. File mẫu test:
- [ ] 2-3 ảnh CCCD mẫu
- [ ] 2-3 MST mẫu
- [ ] 1-2 hồ sơ hoàn chỉnh mẫu

---

## XI. ROADMAP TỔNG QUAN

```
Tuần 1-2: Core (Phân quyền + Zalo OA)
Tuần 3-4: Processing (OCR + MST + Form)
Tuần 5-6: Automation (Phân công + Sheets)
Tuần 7-8: Integration (Test + Deploy)

TỔNG: 8 tuần → Hệ thống hoàn chỉnh
```

---

**END OF SPECIFICATION**

> **Note:** File này dùng làm context cho AI Agent/Cursor Rules  
> Mọi code generation phải tuân thủ spec này
