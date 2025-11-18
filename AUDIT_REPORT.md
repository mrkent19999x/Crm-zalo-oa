# 🔍 BÁO CÁO RÀ SOÁT PROJECT

**Ngày:** 2025-01-18  
**Mục đích:** Kiểm tra conflict giữa code hiện tại và SPECIFICATION.md

---

## I. TỔNG QUAN

### ✅ GIỮ NGUYÊN (OK - Không conflict)

| File/Folder | Lý do |
|-------------|-------|
| `frontend/` | UI đẹp, tái sử dụng được cho dashboard nội bộ |
| `frontend/index.html` | Cấu trúc tốt, chỉ cần sửa nội dung |
| `frontend/styles.css` | CSS đẹp, giữ nguyên |
| `frontend/app.js` | Logic frontend OK, sửa API calls |
| `README.md` | Giữ để tham khảo, update sau |
| `scripts/start.sh` | Script chạy server, OK |
| `tests/test_e2e.py` | Test case tốt, giữ để tham khảo |

### ⚠️ CẦN SỬA (Conflict với spec)

| File | Vấn đề | Cách xử lý |
|------|--------|------------|
| `backend/app.py` dòng 3 | Ghi "Giả lập Zalo OA API" | Sửa thành "Zalo OA Real Integration" |
| `backend/app.py` dòng 27-28 | Demo credentials | Đọc từ .env thật |
| `backend/app.py` dòng 30 | DATABASE in-memory | Giữ tạm, thêm sync Google Sheets sau |
| `backend/app.py` dòng 60-81 | ROLES cũ | Thêm vai trò: ctv, tro_ly, nhan_vien, sale_ngan_hang |
| `backend/app.py` dòng 299-344 | Zalo webhook giả lập | Sửa thành xử lý thật |
| `backend/app.py` dòng 478-486 | OCR giả lập | Sửa thành OCR thật (Google Vision/Tesseract) |

### ❌ CẦN BỎ (Lằng nhằng, không dùng)

**KHÔNG CÓ** - Tất cả files đều có giá trị tái sử dụng!

---

## II. CHI TIẾT CẦN SỬA

### 1. `backend/app.py` - ROLES

**Hiện tại:**
```python
ROLES = {
    'quan_tri_vien': {...},
    'soan_noi_dung': {...},
    'cskh': {...},
    'phan_tich_vien': {...},
    'chuyen_vien_tu_van': {...}
}
```

**Cần sửa thành:**
```python
ROLES = {
    'admin': {
        'name': 'Admin',
        'permissions': ['all'],
        'scope': 'all_leads'
    },
    'tro_ly': {
        'name': 'Trợ lý hệ thống',
        'permissions': ['view_all', 'assign', 'monitor'],
        'scope': 'all_leads'
    },
    'nhan_vien': {
        'name': 'Nhân viên xử lý',
        'permissions': ['view_assigned', 'update_status', 'upload_docs'],
        'scope': 'assigned_only'
    },
    'ctv': {
        'name': 'CTV/Cò',
        'permissions': ['create_lead', 'upload_cccd', 'view_own'],
        'scope': 'own_only'
    },
    'sale_ngan_hang': {
        'name': 'Sale Ngân hàng',
        'permissions': ['view_branch', 'download_docs', 'update_result'],
        'scope': 'branch_only'
    }
}
```

### 2. Lead Model - Cần Thêm Fields

**Cần thêm vào create_lead():**
```python
lead = {
    # ... existing fields ...
    'source': data.get('source'),           # ✅ THÊM
    'branch': data.get('branch'),           # ✅ THÊM
    'loai_hinh': data.get('loai_hinh'),     # ✅ THÊM: ca_nhan|ho_kinh_doanh|doanh_nghiep
    'mst': data.get('mst'),                 # ✅ THÊM
    'loai_vay': data.get('loai_vay'),       # ✅ THÊM: tin_chap|the_chap|sme
    'so_tien_vay': data.get('so_tien_vay'), # ✅ THÊM
    'thoi_han': data.get('thoi_han'),       # ✅ THÊM
    'thu_nhap_thang': data.get('thu_nhap_thang'), # ✅ THÊM
    'dti_ratio': None,                      # ✅ THÊM
    'risk_level': None,                     # ✅ THÊM
    'visibility': {                         # ✅ THÊM
        'ctv': [created_by],
        'staff': [assigned_to],
        'bank': [],
        'admin': True
    }
}
```

### 3. Zalo OA - Thay Demo Bằng Thật

**File:** `backend/app.py` dòng 27-28

**Hiện tại:**
```python
ZALO_OA_ID = os.getenv('ZALO_OA_ID', 'demo_oa_id_12345')
ZALO_ACCESS_TOKEN = os.getenv('ZALO_ACCESS_TOKEN', 'demo_access_token')
```

**Sửa thành:**
```python
# Zalo OA Khách hàng
ZALO_OA_KHACH_ID = os.getenv('ZALO_OA_KHACH_ID')
ZALO_OA_KHACH_TOKEN = os.getenv('ZALO_OA_KHACH_TOKEN')

# Zalo OA Nội bộ
ZALO_OA_NOIBI_ID = os.getenv('ZALO_OA_NOIBI_ID')
ZALO_OA_NOIBI_TOKEN = os.getenv('ZALO_OA_NOIBI_TOKEN')

# Validate
if not all([ZALO_OA_KHACH_ID, ZALO_OA_KHACH_TOKEN, 
            ZALO_OA_NOIBI_ID, ZALO_OA_NOIBI_TOKEN]):
    print("⚠️  WARNING: Zalo OA credentials not found in .env")
    print("   System will run in DEMO mode")
```

### 4. OCR CCCD - Thay Giả Lập Bằng Thật

**File:** `backend/app.py` dòng 478-486

**Hiện tại:**
```python
# Simulate OCR processing
if document['type'] == 'cccd':
    document['ocr_data'] = {
        'ho_ten': 'NGUYỄN VĂN A',  # Hard-coded
        'so_cccd': '001234567890',
        ...
    }
```

**Sửa thành:**
```python
# Real OCR processing
if document['type'] == 'cccd':
    from services.ocr_service import OCRService
    ocr = OCRService()
    ocr_result = ocr.extract_cccd(document['file_path'])
    document['ocr_data'] = ocr_result
    document['status'] = 'verified' if ocr_result else 'failed'
```

---

## III. CẤU TRÚC FOLDER MỚI

### Thêm vào project:

```
workspace/
├── backend/
│   ├── app.py                    # ⚠️ Sửa như trên
│   ├── requirements.txt          # ⚠️ Thêm lib: gspread, python-docx, pytesseract
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py           # ✅ MỚI: Centralized config
│   ├── integrations/             # ✅ MỚI
│   │   ├── __init__.py
│   │   ├── zalo_oa.py           # ✅ Zalo OA real API
│   │   └── google_sheets.py     # ✅ Sync Google Sheets
│   ├── services/                 # ✅ MỚI
│   │   ├── __init__.py
│   │   ├── ocr_service.py       # ✅ OCR CCCD
│   │   ├── tax_service.py       # ✅ Check MST
│   │   ├── form_service.py      # ✅ Điền Word
│   │   ├── risk_service.py      # ✅ Đánh giá rủi ro
│   │   └── assignment_service.py # ✅ Phân công tự động
│   └── templates/                # ✅ MỚI
│       └── vpbank_form.docx     # ✅ Template form
├── frontend/                     # ✅ GIỮ NGUYÊN
├── SPECIFICATION.md              # ✅ Đã tạo
└── AUDIT_REPORT.md              # ✅ File này
```

---

## IV. DEPENDENCIES CẦN THÊM

### File: `backend/requirements.txt`

**Thêm vào:**
```txt
# Google Sheets
gspread==5.12.4
oauth2client==4.1.3

# OCR
pytesseract==0.3.10
Pillow==10.1.0
# Hoặc: google-cloud-vision==3.5.0

# Word processing
python-docx==1.1.0

# Excel (nếu cần)
openpyxl==3.1.2
```

---

## V. ENV VARIABLES CẦN THÊM

### File: `config/.env.example`

**Tạo mới:**
```bash
# Zalo OA Khách hàng
ZALO_OA_KHACH_ID=
ZALO_OA_KHACH_TOKEN=

# Zalo OA Nội bộ
ZALO_OA_NOIBI_ID=
ZALO_OA_NOIBI_TOKEN=

# Google Sheets
GOOGLE_CREDENTIALS_PATH=config/google_credentials.json
GOOGLE_SHEET_NAME=CRM Vay Vốn

# OCR
# Option 1: Pytesseract (free, local)
TESSERACT_PATH=/usr/bin/tesseract

# Option 2: Google Vision (free 1000/month)
GOOGLE_APPLICATION_CREDENTIALS=config/google_vision_credentials.json

# Risk Assessment
DTI_LOW_THRESHOLD=35
DTI_HIGH_THRESHOLD=50

# Secret
SECRET_KEY=your-secret-key-here
```

---

## VI. CHECKLIST TRƯỚC KHI MERGE

### Bước 1: Sửa code hiện tại

- [ ] Sửa ROLES trong `app.py` (5 vai trò mới)
- [ ] Thêm fields vào Lead model
- [ ] Sửa Zalo OA config (2 OA riêng biệt)
- [ ] Update README.md với thông tin mới

### Bước 2: Thêm folders/files mới

- [ ] Tạo `backend/integrations/`
- [ ] Tạo `backend/services/`
- [ ] Tạo `backend/templates/`
- [ ] Tạo `config/.env.example`

### Bước 3: Thêm dependencies

- [ ] Update `requirements.txt`
- [ ] Test install: `pip install -r requirements.txt`

### Bước 4: Test

- [ ] Server vẫn chạy được (demo mode)
- [ ] Frontend vẫn hiển thị OK
- [ ] Không có error khi start

### Bước 5: Commit & Merge

- [ ] `git add .`
- [ ] `git commit -m "feat: add specification and prepare for real integration"`
- [ ] `git checkout main`
- [ ] `git merge cursor/review-repository-content-da22`
- [ ] `git push origin main`

---

## VII. KẾT LUẬN

### ✅ KHÔNG CÓ CONFLICT LỚN

- Code hiện tại là nền tảng tốt
- Chỉ cần SỬA (không phải viết lại)
- Tất cả files đều có giá trị

### 📝 CẦN LÀM

1. **Sửa 6 chỗ** trong `app.py`
2. **Thêm 3 folders** mới (integrations, services, templates)
3. **Thêm dependencies** vào requirements.txt
4. **Tạo .env.example**
5. **Update README.md**

### ⏱️ THỜI GIAN ƯỚC TÍNH

- Sửa code hiện tại: 1-2 giờ
- Thêm structure mới: 30 phút
- Test: 30 phút
- **TỔNG: 2-3 giờ** → Có thể merge vào main ngay hôm nay!

---

**🎯 READY TO MERGE!** Không có gì lằng nhằng cần bỏ.

