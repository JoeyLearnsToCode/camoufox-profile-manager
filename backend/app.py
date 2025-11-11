"""Flask backend application for Camoufox Profile Manager - 多会话支持."""
import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from storage import load_profiles, save_profiles, find_profile, update_profile, delete_profile
from validators import validate_profile
from models import Profile
from session_manager import session_manager

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for localhost frontend


# 自定义日志过滤器：过滤 GET /api/session 返回 200 的访问日志
class SessionGetFilter(logging.Filter):
    """过滤 GET /api/session 返回 200 状态码的请求日志."""
    
    def filter(self, record):
        message = record.getMessage()
        # 只过滤 'GET /api/session HTTP' 且返回 200 的日志
        # 格式示例: "GET /api/session HTTP/1.1" 200 -
        if 'GET /api/session HTTP' in message and '" 200' in message:
            return False
        return True


# 配置 Werkzeug 日志记录器
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(SessionGetFilter())


@app.route('/')
def index():
    """Serve the main web UI."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """Get all profiles."""
    profiles = load_profiles()
    return jsonify(profiles)


@app.route('/api/profiles', methods=['POST'])
def create_profile():
    """Create a new profile."""
    data = request.get_json()
    
    # Validate profile data
    is_valid, error_msg = validate_profile(data)
    if not is_valid:
        return jsonify({"error": "Validation failed", "message": error_msg}), 400
    
    # Check for duplicate name
    existing = find_profile(data['name'])
    if existing:
        return jsonify({"error": "Conflict", "message": f"Profile '{data['name']}' already exists"}), 409
    
    # Add to profiles list
    profiles = load_profiles()
    profiles.append(data)
    save_profiles(profiles)
    
    return jsonify(data), 201


@app.route('/api/profiles/<name>', methods=['GET'])
def get_profile(name):
    """Get a single profile by name."""
    profile = find_profile(name)
    if not profile:
        return jsonify({"error": "Not Found", "message": f"Profile '{name}' not found"}), 404
    
    return jsonify(profile)


@app.route('/api/profiles/<name>', methods=['PUT'])
def update_profile_route(name):
    """Update an existing profile."""
    data = request.get_json()
    
    # Validate profile data
    is_valid, error_msg = validate_profile(data)
    if not is_valid:
        return jsonify({"error": "Validation failed", "message": error_msg}), 400
    
    # Check if profile exists
    if not find_profile(name):
        return jsonify({"error": "Not Found", "message": f"Profile '{name}' not found"}), 404
    
    # Update profile
    success = update_profile(name, data)
    if not success:
        return jsonify({"error": "Internal Server Error", "message": "Failed to update profile"}), 500
    
    return jsonify(data)


@app.route('/api/profiles/<name>', methods=['DELETE'])
def delete_profile_route(name):
    """Delete a profile."""
    # Check if profile exists
    if not find_profile(name):
        return jsonify({"error": "Not Found", "message": f"Profile '{name}' not found"}), 404
    
    # Delete profile
    success = delete_profile(name)
    if not success:
        return jsonify({"error": "Internal Server Error", "message": "Failed to delete profile"}), 500
    
    return '', 204


@app.route('/api/session', methods=['GET'])
def get_session():
    """
    获取所有活跃会话.
    
    当前阶段限制：每个 profile 最多一个会话。
    将来扩展：同一 profile 可以有多个会话。
    
    Returns:
        会话列表（每个包含 session_id, profile_name, status, started_at）
    """
    sessions = session_manager.get_sessions()
    return jsonify(sessions), 200


@app.route('/api/session', methods=['POST'])
def start_session():
    """
    启动新的浏览器会话.
    
    当前阶段限制：如果 profile 已有会话运行，返回 409 错误。
    将来扩展：移除限制后可为同一 profile 启动多实例。
    """
    data = request.get_json()
    profile_name = data.get('profile_name')
    screen_width = data.get('screen_width')
    screen_height = data.get('screen_height')
    
    if not profile_name:
        return jsonify({"error": "Validation failed", "message": "profile_name is required"}), 400
    
    # 查找 profile
    profile = find_profile(profile_name)
    if not profile:
        return jsonify({"error": "Not Found", "message": f"Profile '{profile_name}' not found"}), 404
    
    # 启动会话（带屏幕尺寸参数）
    try:
        session = session_manager.start_session(profile, screen_width, screen_height)
        return jsonify(session), 201
    except RuntimeError as e:
        # 当前阶段限制：profile 已有会话运行
        return jsonify({"error": "Conflict", "message": str(e)}), 409
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": f"Failed to start session: {e}"}), 500


@app.route('/api/session', methods=['DELETE'])
def stop_session():
    """
    停止指定的浏览器会话.
    
    Request body:
        {"session_id": "profile-a-1699999999"}
    """
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "Validation failed", "message": "session_id is required"}), 400
    
    try:
        session_manager.stop_session(session_id)
        return '', 204
    except RuntimeError as e:
        return jsonify({"error": "Not Found", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": f"Failed to stop session: {e}"}), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
