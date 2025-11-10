"""Flask backend application for Camoufox Profile Manager."""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from storage import load_profiles, save_profiles, find_profile, update_profile, delete_profile
from validators import validate_profile
from models import Profile
from session_manager import session_manager

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for localhost frontend


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
    """Get current session status."""
    session = session_manager.get_session()
    if session is None:
        # Return null instead of 404 to avoid console errors
        return jsonify(None), 200
    return jsonify(session)


@app.route('/api/session', methods=['POST'])
def start_session():
    """Start a browser session."""
    data = request.get_json()
    profile_name = data.get('profile_name')
    screen_width = data.get('screen_width')
    screen_height = data.get('screen_height')
    
    if not profile_name:
        return jsonify({"error": "Validation failed", "message": "profile_name is required"}), 400
    
    # Find profile
    profile = find_profile(profile_name)
    if not profile:
        return jsonify({"error": "Not Found", "message": f"Profile '{profile_name}' not found"}), 404
    
    # Start session with optional screen dimensions
    try:
        session = session_manager.start_session(profile, screen_width, screen_height)
        return jsonify(session), 201
    except RuntimeError as e:
        return jsonify({"error": "Conflict", "message": str(e)}), 409
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": f"Failed to start session: {e}"}), 500


@app.route('/api/session', methods=['DELETE'])
def stop_session():
    """Stop the current browser session."""
    try:
        session_manager.stop_session()
        return '', 204
    except RuntimeError as e:
        return jsonify({"error": "Not Found", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": f"Failed to stop session: {e}"}), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
