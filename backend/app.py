"""
Zalo OA Finance Workflow - Backend API Server
Giả lập Zalo OA API + Quản lý Workflow Tư Vấn Tài Chính
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import jwt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'zalo-oa-finance-secret-key-2025')
ZALO_OA_ID = os.getenv('ZALO_OA_ID', 'demo_oa_id_12345')
ZALO_ACCESS_TOKEN = os.getenv('ZALO_ACCESS_TOKEN', 'demo_access_token')

# In-memory database simulation
DATABASE = {
    'users': {},
    'leads': {},
    'conversations': {},
    'documents': {},
    'notifications': {},
    'workflow_status': {},
    'chatbot_intents': {},
    'broadcast_messages': [],
    'analytics': {
        'total_leads': 0,
        'messages_sent': 0,
        'documents_processed': 0,
        'active_conversations': 0
    }
}

# Default admin user
DATABASE['users']['admin'] = {
    'id': 'admin',
    'username': 'admin',
    'password': hashlib.sha256('admin123'.encode()).hexdigest(),
    'role': 'quan_tri_vien',
    'name': 'Quản Trị Viên',
    'email': 'admin@demo.vn',
    'created_at': datetime.now().isoformat()
}

# Predefined roles
ROLES = {
    'quan_tri_vien': {
        'name': 'Quản trị viên',
        'permissions': ['all']
    },
    'soan_noi_dung': {
        'name': 'Soạn nội dung',
        'permissions': ['manage_content', 'send_broadcast', 'reply_chat']
    },
    'cskh': {
        'name': 'CSKH',
        'permissions': ['reply_chat', 'view_leads', 'update_lead_status']
    },
    'phan_tich_vien': {
        'name': 'Phân tích viên',
        'permissions': ['view_analytics', 'export_reports']
    },
    'chuyen_vien_tu_van': {
        'name': 'Chuyên viên tư vấn',
        'permissions': ['reply_chat', 'view_leads', 'update_lead_status', 'process_documents']
    }
}

# Chatbot intents for financial consultation
CHATBOT_INTENTS = {
    'chao_hoi': {
        'patterns': ['xin chào', 'hello', 'hi', 'chào', 'alo'],
        'responses': [
            'Xin chào! Tôi là trợ lý tư vấn tài chính. Tôi có thể giúp gì cho bạn?',
            'Chào bạn! Rất vui được hỗ trợ bạn về các dịch vụ tài chính.'
        ]
    },
    'dang_ky_tu_van': {
        'patterns': ['đăng ký', 'tư vấn', 'muốn tư vấn', 'cần tư vấn'],
        'responses': [
            'Để đăng ký tư vấn, vui lòng cung cấp:\n1. Họ tên\n2. Số điện thoại\n3. Nhu cầu tài chính',
            'Bạn muốn tư vấn về:\n• Vay vốn\n• Bảo hiểm\n• Đầu tư\n• Tiết kiệm\nVui lòng chọn dịch vụ.'
        ]
    },
    'san_pham': {
        'patterns': ['sản phẩm', 'dịch vụ', 'có gì', 'cung cấp'],
        'responses': [
            'Chúng tôi cung cấp:\n✅ Vay tiêu dùng\n✅ Bảo hiểm nhân thọ\n✅ Đầu tư chứng khoán\n✅ Tiết kiệm lãi suất cao'
        ]
    },
    'ho_so': {
        'patterns': ['hồ sơ', 'giấy tờ', 'cần gì', 'thủ tục'],
        'responses': [
            'Hồ sơ cần thiết:\n📋 CCCD/CMND\n📋 Sổ hộ khẩu\n📋 Giấy xác nhận thu nhập\n📋 Hợp đồng lao động (nếu có)'
        ]
    },
    'lien_he_nhan_vien': {
        'patterns': ['gặp nhân viên', 'nói chuyện', 'người thật', 'hotline'],
        'responses': [
            'Tôi sẽ chuyển bạn đến chuyên viên tư vấn ngay. Vui lòng chờ trong giây lát...'
        ],
        'action': 'transfer_to_agent'
    },
    'cam_on': {
        'patterns': ['cảm ơn', 'thank', 'thanks'],
        'responses': [
            'Cảm ơn bạn đã liên hệ! Chúc bạn một ngày tốt lành! 🌟'
        ]
    }
}

DATABASE['chatbot_intents'] = CHATBOT_INTENTS

# JWT Token helper
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token không hợp lệ'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = DATABASE['users'].get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User không tồn tại'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token hết hạn'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token không hợp lệ'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# ======================= AUTH ENDPOINTS =======================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Đăng nhập"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = DATABASE['users'].get(username)
    if not user:
        return jsonify({'error': 'Tài khoản không tồn tại'}), 401
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if user['password'] != hashed_password:
        return jsonify({'error': 'Mật khẩu không đúng'}), 401
    
    token = generate_token(username)
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'role': user['role'],
            'email': user['email']
        }
    })

@app.route('/api/auth/register', methods=['POST'])
@token_required
def register(current_user):
    """Đăng ký user mới (chỉ admin)"""
    if current_user['role'] != 'quan_tri_vien':
        return jsonify({'error': 'Không có quyền'}), 403
    
    data = request.json
    username = data.get('username')
    
    if username in DATABASE['users']:
        return jsonify({'error': 'Username đã tồn tại'}), 400
    
    DATABASE['users'][username] = {
        'id': username,
        'username': username,
        'password': hashlib.sha256(data.get('password', '123456').encode()).hexdigest(),
        'role': data.get('role', 'cskh'),
        'name': data.get('name', ''),
        'email': data.get('email', ''),
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({'message': 'Tạo user thành công', 'user_id': username})

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Lấy thông tin user hiện tại"""
    return jsonify({
        'id': current_user['id'],
        'username': current_user['username'],
        'name': current_user['name'],
        'role': current_user['role'],
        'email': current_user['email'],
        'role_info': ROLES.get(current_user['role'], {})
    })

# ======================= LEAD MANAGEMENT =======================

@app.route('/api/leads', methods=['GET'])
@token_required
def get_leads(current_user):
    """Lấy danh sách leads"""
    leads = list(DATABASE['leads'].values())
    # Sort by created_at desc
    leads.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(leads)

@app.route('/api/leads', methods=['POST'])
@token_required
def create_lead(current_user):
    """Tạo lead mới"""
    data = request.json
    lead_id = str(uuid.uuid4())[:8]
    
    lead = {
        'id': lead_id,
        'name': data.get('name', ''),
        'phone': data.get('phone', ''),
        'email': data.get('email', ''),
        'source': data.get('source', 'zalo_oa'),
        'product_interest': data.get('product_interest', ''),
        'status': 'tiep_nhan',  # tiep_nhan, dang_xu_ly, cho_bo_sung, hoan_thanh
        'assigned_to': data.get('assigned_to', ''),
        'labels': data.get('labels', []),
        'notes': data.get('notes', ''),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'created_by': current_user['id']
    }
    
    DATABASE['leads'][lead_id] = lead
    DATABASE['analytics']['total_leads'] += 1
    
    # Emit realtime update
    socketio.emit('new_lead', lead, namespace='/dashboard')
    
    return jsonify(lead), 201

@app.route('/api/leads/<lead_id>', methods=['PUT'])
@token_required
def update_lead(current_user, lead_id):
    """Cập nhật lead"""
    if lead_id not in DATABASE['leads']:
        return jsonify({'error': 'Lead không tồn tại'}), 404
    
    data = request.json
    lead = DATABASE['leads'][lead_id]
    
    # Update fields
    for key in ['name', 'phone', 'email', 'status', 'assigned_to', 'labels', 'notes', 'product_interest']:
        if key in data:
            lead[key] = data[key]
    
    lead['updated_at'] = datetime.now().isoformat()
    DATABASE['leads'][lead_id] = lead
    
    # Emit realtime update
    socketio.emit('lead_updated', lead, namespace='/dashboard')
    
    return jsonify(lead)

@app.route('/api/leads/<lead_id>', methods=['DELETE'])
@token_required
def delete_lead(current_user, lead_id):
    """Xóa lead"""
    if current_user['role'] not in ['quan_tri_vien']:
        return jsonify({'error': 'Không có quyền'}), 403
    
    if lead_id in DATABASE['leads']:
        del DATABASE['leads'][lead_id]
        return jsonify({'message': 'Đã xóa lead'})
    
    return jsonify({'error': 'Lead không tồn tại'}), 404

# ======================= ZALO OA SIMULATOR =======================

@app.route('/api/zalo/webhook', methods=['POST'])
def zalo_webhook():
    """Webhook nhận sự kiện từ Zalo OA (giả lập)"""
    data = request.json
    event_type = data.get('event_name', 'user_send_text')
    
    if event_type == 'user_send_text':
        # Process incoming message
        user_id = data.get('sender', {}).get('id', str(uuid.uuid4())[:8])
        message = data.get('message', {}).get('text', '')
        
        # Save conversation
        if user_id not in DATABASE['conversations']:
            DATABASE['conversations'][user_id] = {
                'user_id': user_id,
                'messages': [],
                'created_at': datetime.now().isoformat()
            }
        
        DATABASE['conversations'][user_id]['messages'].append({
            'sender': 'user',
            'text': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Process with chatbot
        response = process_chatbot_message(message)
        
        DATABASE['conversations'][user_id]['messages'].append({
            'sender': 'bot',
            'text': response['text'],
            'timestamp': datetime.now().isoformat()
        })
        
        # Emit to dashboard
        socketio.emit('new_message', {
            'user_id': user_id,
            'message': message,
            'response': response
        }, namespace='/dashboard')
        
        return jsonify(response)
    
    return jsonify({'status': 'ok'})

@app.route('/api/zalo/send-message', methods=['POST'])
@token_required
def send_zalo_message(current_user):
    """Gửi tin nhắn qua Zalo OA (giả lập)"""
    data = request.json
    recipient_id = data.get('recipient_id')
    message = data.get('message')
    
    if recipient_id not in DATABASE['conversations']:
        DATABASE['conversations'][recipient_id] = {
            'user_id': recipient_id,
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
    
    DATABASE['conversations'][recipient_id]['messages'].append({
        'sender': 'agent',
        'text': message,
        'timestamp': datetime.now().isoformat(),
        'sent_by': current_user['id']
    })
    
    DATABASE['analytics']['messages_sent'] += 1
    
    return jsonify({
        'status': 'sent',
        'message_id': str(uuid.uuid4())[:8],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/zalo/broadcast', methods=['POST'])
@token_required
def send_broadcast(current_user):
    """Gửi tin nhắn broadcast (giả lập)"""
    if 'send_broadcast' not in ROLES.get(current_user['role'], {}).get('permissions', []) and current_user['role'] != 'quan_tri_vien':
        return jsonify({'error': 'Không có quyền'}), 403
    
    data = request.json
    broadcast = {
        'id': str(uuid.uuid4())[:8],
        'title': data.get('title', ''),
        'content': data.get('content', ''),
        'target_audience': data.get('target_audience', 'all'),
        'scheduled_time': data.get('scheduled_time', datetime.now().isoformat()),
        'status': 'scheduled',
        'sent_count': 0,
        'created_by': current_user['id'],
        'created_at': datetime.now().isoformat()
    }
    
    DATABASE['broadcast_messages'].append(broadcast)
    
    return jsonify(broadcast), 201

@app.route('/api/zalo/conversations', methods=['GET'])
@token_required
def get_conversations(current_user):
    """Lấy danh sách hội thoại"""
    return jsonify(list(DATABASE['conversations'].values()))

@app.route('/api/zalo/conversations/<user_id>', methods=['GET'])
@token_required
def get_conversation(current_user, user_id):
    """Lấy chi tiết hội thoại"""
    if user_id not in DATABASE['conversations']:
        return jsonify({'error': 'Conversation không tồn tại'}), 404
    
    return jsonify(DATABASE['conversations'][user_id])

def process_chatbot_message(message):
    """Xử lý tin nhắn với chatbot AI"""
    message_lower = message.lower()
    
    # Find matching intent
    for intent_key, intent_data in CHATBOT_INTENTS.items():
        for pattern in intent_data['patterns']:
            if pattern in message_lower:
                import random
                response_text = random.choice(intent_data['responses'])
                
                result = {
                    'text': response_text,
                    'intent': intent_key,
                    'confidence': 0.85
                }
                
                if intent_data.get('action') == 'transfer_to_agent':
                    result['action'] = 'transfer_to_agent'
                
                return result
    
    # Default response
    return {
        'text': 'Cảm ơn bạn đã liên hệ. Tôi chưa hiểu rõ yêu cầu của bạn. Bạn có thể:\n1. Đăng ký tư vấn\n2. Xem sản phẩm\n3. Hỏi về hồ sơ\n4. Gặp nhân viên',
        'intent': 'unknown',
        'confidence': 0.3
    }

# ======================= DOCUMENT MANAGEMENT =======================

@app.route('/api/documents', methods=['GET'])
@token_required
def get_documents(current_user):
    """Lấy danh sách hồ sơ"""
    docs = list(DATABASE['documents'].values())
    docs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(docs)

@app.route('/api/documents', methods=['POST'])
@token_required
def upload_document(current_user):
    """Upload hồ sơ (giả lập)"""
    data = request.json
    doc_id = str(uuid.uuid4())[:8]
    
    document = {
        'id': doc_id,
        'lead_id': data.get('lead_id', ''),
        'type': data.get('type', 'cccd'),  # cccd, dkkd, thue, hop_dong, khac
        'filename': data.get('filename', ''),
        'file_size': data.get('file_size', 0),
        'status': 'pending',  # pending, processing, verified, rejected
        'ocr_data': {},
        'notes': data.get('notes', ''),
        'created_at': datetime.now().isoformat(),
        'created_by': current_user['id']
    }
    
    DATABASE['documents'][doc_id] = document
    DATABASE['analytics']['documents_processed'] += 1
    
    # Simulate OCR processing
    if document['type'] == 'cccd':
        document['ocr_data'] = {
            'ho_ten': 'NGUYỄN VĂN A',
            'so_cccd': '001234567890',
            'ngay_sinh': '01/01/1990',
            'gioi_tinh': 'Nam',
            'dia_chi': '123 Đường ABC, Quận XYZ, TP.HCM'
        }
        document['status'] = 'verified'
    
    return jsonify(document), 201

@app.route('/api/documents/<doc_id>/ocr', methods=['POST'])
@token_required
def process_ocr(current_user, doc_id):
    """Xử lý OCR cho hồ sơ (giả lập)"""
    if doc_id not in DATABASE['documents']:
        return jsonify({'error': 'Document không tồn tại'}), 404
    
    doc = DATABASE['documents'][doc_id]
    doc['status'] = 'processing'
    
    # Simulate OCR result
    if doc['type'] == 'cccd':
        doc['ocr_data'] = {
            'ho_ten': 'NGUYỄN VĂN DEMO',
            'so_cccd': '001' + str(uuid.uuid4().int)[:9],
            'ngay_sinh': '15/06/1985',
            'gioi_tinh': 'Nam',
            'dia_chi': '456 Đường Demo, Quận Test, TP.HCM',
            'ngay_cap': '01/01/2020',
            'noi_cap': 'Cục QLHC về TTXH'
        }
    elif doc['type'] == 'dkkd':
        doc['ocr_data'] = {
            'ten_doanh_nghiep': 'CÔNG TY TNHH DEMO',
            'mst': '0312' + str(uuid.uuid4().int)[:6],
            'dia_chi': '789 Đường Test, Quận ABC, TP.HCM',
            'nguoi_dai_dien': 'NGUYỄN VĂN DEMO',
            'ngay_cap': '01/01/2022'
        }
    
    doc['status'] = 'verified'
    DATABASE['documents'][doc_id] = doc
    
    return jsonify(doc)

# ======================= NOTIFICATIONS =======================

@app.route('/api/notifications/templates', methods=['GET'])
@token_required
def get_notification_templates(current_user):
    """Lấy mẫu thông báo tự động"""
    templates = {
        'chao_mung': {
            'name': 'Chào mừng khách hàng',
            'content': 'Chào {ten_khach_hang}, cảm ơn bạn đã quan tâm đến {ten_doanh_nghiep}! Chúng tôi luôn sẵn sàng hỗ trợ bạn.',
            'channels': ['zalo_oa', 'email']
        },
        'xac_nhan_yeu_cau': {
            'name': 'Xác nhận nhận yêu cầu',
            'content': 'Cảm ơn bạn đã liên hệ với {ten_doanh_nghiep}. Chúng tôi đã nhận được yêu cầu và sẽ phản hồi sớm nhất.',
            'channels': ['zalo_oa', 'email']
        },
        'nhac_bo_sung': {
            'name': 'Nhắc bổ sung hồ sơ',
            'content': 'Bạn vui lòng bổ sung {tai_lieu} để hoàn tất hồ sơ. Nếu cần hỗ trợ, liên hệ {so_dien_thoai}.',
            'channels': ['zalo_oa', 'email']
        },
        'phe_duyet': {
            'name': 'Thông báo phê duyệt',
            'content': 'Hồ sơ của bạn đã được phê duyệt. Vui lòng kiểm tra email để nhận hợp đồng/phiếu xác nhận.',
            'channels': ['zalo_oa', 'email']
        },
        'nhac_lich_hen': {
            'name': 'Nhắc lịch hẹn',
            'content': 'Bạn có lịch hẹn với {ten_doanh_nghiep} vào {ngay_gio}. Vui lòng đến đúng giờ để được phục vụ tốt nhất.',
            'channels': ['zalo_oa', 'email']
        },
        'nhac_thanh_toan': {
            'name': 'Nhắc thanh toán',
            'content': 'Hóa đơn {ma_hoa_don} của bạn sẽ đến hạn vào {ngay}. Vui lòng thanh toán để tránh gián đoạn dịch vụ.',
            'channels': ['zalo_oa', 'email']
        }
    }
    return jsonify(templates)

@app.route('/api/notifications/send', methods=['POST'])
@token_required
def send_notification(current_user):
    """Gửi thông báo"""
    data = request.json
    notification = {
        'id': str(uuid.uuid4())[:8],
        'template': data.get('template', ''),
        'recipient_id': data.get('recipient_id', ''),
        'channel': data.get('channel', 'zalo_oa'),
        'content': data.get('content', ''),
        'status': 'sent',
        'sent_at': datetime.now().isoformat(),
        'sent_by': current_user['id']
    }
    
    DATABASE['notifications'][notification['id']] = notification
    
    return jsonify(notification), 201

# ======================= ANALYTICS =======================

@app.route('/api/analytics/dashboard', methods=['GET'])
@token_required
def get_dashboard_analytics(current_user):
    """Lấy thống kê dashboard"""
    # Calculate real stats
    total_leads = len(DATABASE['leads'])
    active_conversations = len(DATABASE['conversations'])
    documents_processed = len(DATABASE['documents'])
    messages_sent = DATABASE['analytics']['messages_sent']
    
    # Calculate lead status breakdown
    lead_by_status = {}
    for lead in DATABASE['leads'].values():
        status = lead.get('status', 'unknown')
        lead_by_status[status] = lead_by_status.get(status, 0) + 1
    
    # Recent activity
    recent_leads = sorted(
        DATABASE['leads'].values(),
        key=lambda x: x.get('created_at', ''),
        reverse=True
    )[:5]
    
    return jsonify({
        'stats': {
            'total_leads': total_leads,
            'new_leads_today': sum(1 for l in DATABASE['leads'].values() 
                                   if l.get('created_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))),
            'active_conversations': active_conversations,
            'messages_sent': messages_sent,
            'documents_processed': documents_processed,
            'pending_documents': sum(1 for d in DATABASE['documents'].values() if d.get('status') == 'pending')
        },
        'lead_by_status': lead_by_status,
        'recent_leads': recent_leads,
        'conversion_rate': round((lead_by_status.get('hoan_thanh', 0) / max(total_leads, 1)) * 100, 2)
    })

@app.route('/api/analytics/reports', methods=['GET'])
@token_required
def generate_reports(current_user):
    """Xuất báo cáo"""
    report_type = request.args.get('type', 'summary')
    
    if report_type == 'summary':
        return jsonify({
            'report_type': 'summary',
            'generated_at': datetime.now().isoformat(),
            'data': {
                'total_leads': len(DATABASE['leads']),
                'total_conversations': len(DATABASE['conversations']),
                'total_documents': len(DATABASE['documents']),
                'total_notifications': len(DATABASE['notifications']),
                'users': len(DATABASE['users'])
            }
        })
    
    return jsonify({'error': 'Report type not supported'}), 400

# ======================= USER MANAGEMENT =======================

@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    """Lấy danh sách users"""
    if current_user['role'] != 'quan_tri_vien':
        return jsonify({'error': 'Không có quyền'}), 403
    
    users = []
    for user in DATABASE['users'].values():
        users.append({
            'id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'role': user['role'],
            'email': user['email'],
            'created_at': user['created_at']
        })
    
    return jsonify(users)

@app.route('/api/users/<user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """Cập nhật user"""
    if current_user['role'] != 'quan_tri_vien':
        return jsonify({'error': 'Không có quyền'}), 403
    
    if user_id not in DATABASE['users']:
        return jsonify({'error': 'User không tồn tại'}), 404
    
    data = request.json
    user = DATABASE['users'][user_id]
    
    for key in ['name', 'email', 'role']:
        if key in data:
            user[key] = data[key]
    
    if 'password' in data and data['password']:
        user['password'] = hashlib.sha256(data['password'].encode()).hexdigest()
    
    DATABASE['users'][user_id] = user
    
    return jsonify({'message': 'Cập nhật thành công'})

@app.route('/api/roles', methods=['GET'])
@token_required
def get_roles(current_user):
    """Lấy danh sách vai trò"""
    return jsonify(ROLES)

# ======================= WORKFLOW STATUS =======================

@app.route('/api/workflow/<lead_id>/status', methods=['GET'])
@token_required
def get_workflow_status(current_user, lead_id):
    """Lấy trạng thái workflow của lead"""
    if lead_id not in DATABASE['leads']:
        return jsonify({'error': 'Lead không tồn tại'}), 404
    
    lead = DATABASE['leads'][lead_id]
    workflow = DATABASE['workflow_status'].get(lead_id, {
        'lead_id': lead_id,
        'steps': [
            {'step': 'tiep_nhan', 'status': 'completed', 'timestamp': lead.get('created_at')},
            {'step': 'phan_loai', 'status': 'pending', 'timestamp': None},
            {'step': 'tu_van', 'status': 'pending', 'timestamp': None},
            {'step': 'xu_ly_ho_so', 'status': 'pending', 'timestamp': None},
            {'step': 'phe_duyet', 'status': 'pending', 'timestamp': None},
            {'step': 'hoan_thanh', 'status': 'pending', 'timestamp': None}
        ]
    })
    
    return jsonify(workflow)

@app.route('/api/workflow/<lead_id>/advance', methods=['POST'])
@token_required
def advance_workflow(current_user, lead_id):
    """Chuyển bước workflow"""
    if lead_id not in DATABASE['leads']:
        return jsonify({'error': 'Lead không tồn tại'}), 404
    
    data = request.json
    next_step = data.get('next_step')
    
    if lead_id not in DATABASE['workflow_status']:
        DATABASE['workflow_status'][lead_id] = {
            'lead_id': lead_id,
            'steps': [
                {'step': 'tiep_nhan', 'status': 'completed', 'timestamp': datetime.now().isoformat()},
                {'step': 'phan_loai', 'status': 'pending', 'timestamp': None},
                {'step': 'tu_van', 'status': 'pending', 'timestamp': None},
                {'step': 'xu_ly_ho_so', 'status': 'pending', 'timestamp': None},
                {'step': 'phe_duyet', 'status': 'pending', 'timestamp': None},
                {'step': 'hoan_thanh', 'status': 'pending', 'timestamp': None}
            ]
        }
    
    workflow = DATABASE['workflow_status'][lead_id]
    
    for step in workflow['steps']:
        if step['step'] == next_step:
            step['status'] = 'completed'
            step['timestamp'] = datetime.now().isoformat()
            break
    
    DATABASE['workflow_status'][lead_id] = workflow
    
    # Update lead status
    status_map = {
        'phan_loai': 'dang_xu_ly',
        'tu_van': 'dang_xu_ly',
        'xu_ly_ho_so': 'cho_bo_sung',
        'phe_duyet': 'cho_bo_sung',
        'hoan_thanh': 'hoan_thanh'
    }
    
    if next_step in status_map:
        DATABASE['leads'][lead_id]['status'] = status_map[next_step]
        DATABASE['leads'][lead_id]['updated_at'] = datetime.now().isoformat()
    
    return jsonify(workflow)

# ======================= STATIC FILES =======================

@app.route('/')
def serve_frontend():
    """Serve frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)

# ======================= SOCKET.IO EVENTS =======================

@socketio.on('connect', namespace='/dashboard')
def handle_connect():
    print('Client connected to dashboard')
    emit('connected', {'status': 'ok'})

@socketio.on('disconnect', namespace='/dashboard')
def handle_disconnect():
    print('Client disconnected from dashboard')

@socketio.on('join_lead_room', namespace='/dashboard')
def handle_join_lead_room(data):
    lead_id = data.get('lead_id')
    join_room(f'lead_{lead_id}')
    emit('joined', {'room': f'lead_{lead_id}'})

@socketio.on('chat_message', namespace='/dashboard')
def handle_chat_message(data):
    """Handle chat message from simulator"""
    user_id = data.get('user_id', 'test_user')
    message = data.get('message', '')
    
    # Process message
    webhook_data = {
        'event_name': 'user_send_text',
        'sender': {'id': user_id},
        'message': {'text': message}
    }
    
    # Simulate webhook processing
    if user_id not in DATABASE['conversations']:
        DATABASE['conversations'][user_id] = {
            'user_id': user_id,
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
    
    DATABASE['conversations'][user_id]['messages'].append({
        'sender': 'user',
        'text': message,
        'timestamp': datetime.now().isoformat()
    })
    
    # Get bot response
    response = process_chatbot_message(message)
    
    DATABASE['conversations'][user_id]['messages'].append({
        'sender': 'bot',
        'text': response['text'],
        'timestamp': datetime.now().isoformat()
    })
    
    # Emit response
    emit('bot_response', {
        'user_id': user_id,
        'message': message,
        'response': response
    })

# ======================= MAIN =======================

if __name__ == '__main__':
    print("=" * 50)
    print("Zalo OA Finance Workflow Server")
    print("=" * 50)
    print(f"Server running on http://localhost:5000")
    print(f"Default login: admin / admin123")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
