# Zalo OA Financial Advisory Workflow

Hệ thống quản lý quy trình tư vấn tài chính trên nền tảng Zalo OA (Official Account).

## Tính năng chính

- **Quản lý Lead**: CRUD đầy đủ, theo dõi trạng thái khách hàng
- **Chatbot AI**: Tự động phân tích ý định và phản hồi thông minh
- **Tích hợp Zalo OA**: Gửi/nhận tin nhắn, webhook events
- **OCR Documents**: Trích xuất thông tin từ CCCD, giấy phép kinh doanh
- **Workflow Automation**: Quy trình end-to-end từ tiếp nhận đến hoàn thành
- **Analytics Dashboard**: Báo cáo, thống kê real-time
- **Role-based Access**: Phân quyền Admin, Manager, Advisor, Support

## Cài đặt

```bash
# Clone repo
git clone <repo-url>
cd zalo-oa-finance-workflow

# Cài đặt dependencies
uv pip install -r backend/requirements.txt

# Cấu hình môi trường
cp config/.env.example config/.env
# Chỉnh sửa .env với thông tin thật

# Chạy server
python backend/app.py
```

## Test

```bash
# Chạy E2E tests
python tests/test_e2e.py
```

## Cấu trúc project

```
├── backend/          # Flask API server
│   ├── app.py        # Main application
│   └── requirements.txt
├── frontend/         # Web dashboard
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── config/           # Configuration files
│   └── .env.example
├── tests/            # Test suites
│   └── test_e2e.py
└── scripts/          # Utility scripts
    └── start.sh
```

## Demo Mode

Hệ thống chạy ở chế độ demo với Zalo OA simulator. Để chuyển sang production, cập nhật credentials trong file `.env`.

**Demo login**: admin / admin123

## Author

MiniMax Agent

## License

Private - All rights reserved
