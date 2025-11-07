"""JSON file storage for profiles."""
import json
import os
from typing import List, Dict, Any, Optional
from models import Profile

PROFILES_FILE = "profiles.json"


def load_profiles() -> List[Dict[str, Any]]:
    """
    Load profiles from profiles.json.
    Returns empty list if file missing or corrupted.
    """
    if not os.path.exists(PROFILES_FILE):
        return []
    
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Corrupted file - backup and return empty
        print(f"[!] Warning: profiles.json corrupted ({e}). Creating backup.")
        backup_corrupted_file()
        return []


def save_profiles(profiles: List[Dict[str, Any]]) -> None:
    """
    Save profiles to profiles.json with atomic write.
    Uses temp file + rename for safety.
    """
    temp_path = f"{PROFILES_FILE}.tmp"
    
    try:
        # Write to temp file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        
        # Atomic rename (overwrites existing)
        os.replace(temp_path, PROFILES_FILE)
    except IOError as e:
        print(f"[!] Error saving profiles: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def find_profile(name: str) -> Optional[Dict[str, Any]]:
    """
    Find profile by name.
    Returns None if not found.
    """
    profiles = load_profiles()
    return next((p for p in profiles if p.get('name') == name), None)


def update_profile(name: str, updated_data: Dict[str, Any]) -> bool:
    """
    Update profile by name.
    Returns True if successful, False if profile not found.
    """
    profiles = load_profiles()
    
    for i, p in enumerate(profiles):
        if p.get('name') == name:
            profiles[i] = updated_data
            save_profiles(profiles)
            return True
    
    return False


def delete_profile(name: str) -> bool:
    """
    Delete profile by name.
    Returns True if successful, False if profile not found.
    """
    profiles = load_profiles()
    original_count = len(profiles)
    
    profiles = [p for p in profiles if p.get('name') != name]
    
    if len(profiles) < original_count:
        save_profiles(profiles)
        return True
    
    return False


def backup_corrupted_file() -> None:
    """Backup corrupted profiles.json file."""
    if os.path.exists(PROFILES_FILE):
        backup_path = f"{PROFILES_FILE}.backup"
        try:
            os.replace(PROFILES_FILE, backup_path)
            print(f"[✓] Backed up corrupted file to {backup_path}")
        except IOError:
            pass
