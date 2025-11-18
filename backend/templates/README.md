# Templates

Folder này chứa các template file Word để tự động điền hồ sơ.

## Sử dụng:

1. Đặt file template Word (`.docx`) vào đây
2. Trong file Word, dùng placeholder format: `{{TEN_FIELD}}`
3. Ví dụ: `{{HO_TEN}}`, `{{SO_CCCD}}`, `{{DIA_CHI}}`
4. Service sẽ tự động replace placeholder bằng data thật

## Template cần có:

- `vpbank_form.docx` - Form đăng ký vay VPBank
- `risk_report.docx` - Báo cáo đánh giá rủi ro (optional)
