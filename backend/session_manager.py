"""Camoufox browser session management with threading."""
import os
import time
import threading
from typing import Optional, Dict, Any
from datetime import datetime


class SessionManager:
    """Manages Camoufox browser sessions."""
    
    def __init__(self):
        self.active_session: Optional[Dict[str, Any]] = None
        self.browser_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._context = None
    
    def start_session(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new Camoufox browser session.
        
        Args:
            profile: Profile dictionary with configuration
        
        Returns:
            Session dictionary with status
        
        Raises:
            RuntimeError: If session is already running
        """
        if self.active_session is not None:
            raise RuntimeError(f"Session already running for '{self.active_session['profile_name']}'")
        
        # Clear stop flag
        self._stop_flag.clear()
        
        # Create session record
        self.active_session = {
            'profile_name': profile['name'],
            'status': 'starting',
            'started_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Start browser in background thread
        self.browser_thread = threading.Thread(
            target=self._run_browser,
            args=(profile,),
            daemon=True
        )
        self.browser_thread.start()
        
        # Wait a moment for browser to start
        time.sleep(1)
        
        # Update status
        self.active_session['status'] = 'running'
        
        return self.active_session.copy()
    
    def stop_session(self) -> None:
        """Stop the current browser session."""
        if self.active_session is None:
            raise RuntimeError("No active session to stop")
        
        # Signal thread to stop
        self._stop_flag.set()
        
        # Update status
        self.active_session['status'] = 'stopping'
        
        # Wait for thread to finish (with timeout)
        if self.browser_thread and self.browser_thread.is_alive():
            self.browser_thread.join(timeout=5)
        
        # Clean up
        if self._context is not None:
            try:
                self._context.close()
                try:
                    self._context.__exit__(None, None, None)
                except Exception:
                    pass
            except Exception as e:
                print(f"[!] Error closing Camoufox context: {e}")
            finally:
                self._context = None
        
        # Clear session
        self.active_session = None
        self.browser_thread = None
    
    def get_session(self) -> Optional[Dict[str, Any]]:
        """Get current session status."""
        return self.active_session.copy() if self.active_session else None
    
    def _run_browser(self, profile: Dict[str, Any]) -> None:
        """
        Run Camoufox browser in background thread.
        Ported from main_window.py CamoufoxWorker logic.
        """
        try:
            from camoufox.sync_api import Camoufox
        except ImportError:
            print("[!] Camoufox not installed")
            return
        
        try:
            # Get viewport size
            width = profile.get('viewport_width', 1280)
            height = profile.get('viewport_height', 800)
            
            # Build Camoufox options
            opts = {
                'headless': False,
                'window': (width + 2, height + 88),
            }
            
            # Persistent context
            if profile.get('persistent_dir'):
                os.makedirs(profile['persistent_dir'], exist_ok=True)
                opts['persistent_context'] = True
                opts['user_data_dir'] = os.path.abspath(profile['persistent_dir'])
            
            # Proxy configuration
            proxy_config = profile.get('proxy', {})
            if proxy_config.get('host') and proxy_config.get('port'):
                proxy_dict = {
                    'server': f"http://{proxy_config['host']}:{proxy_config['port']}"
                }
                if proxy_config.get('username'):
                    proxy_dict['username'] = proxy_config['username']
                if proxy_config.get('password'):
                    proxy_dict['password'] = proxy_config['password']
                
                opts['proxy'] = proxy_dict
                
                # GeoIP if enabled
                if profile.get('use_geoip'):
                    opts['geoip'] = True
            
            # Launch browser
            self._context = Camoufox(**opts).__enter__()
            
            # Get or create page
            pages = list(getattr(self._context, 'pages', []))
            if pages:
                page = pages[0]
                # Close extra pages
                for extra in pages[1:]:
                    try:
                        extra.close()
                    except Exception:
                        pass
            else:
                page = self._context.new_page()
            
            # Set viewport
            try:
                page.set_viewport_size({'width': width, 'height': height})
            except Exception:
                pass
            
            # Fullscreen if enabled
            if profile.get('fullscreen'):
                try:
                    page.keyboard.press('F11')
                except Exception:
                    pass
            
            # Keep browser running until stop signal
            while not self._stop_flag.is_set():
                time.sleep(0.5)
        
        except Exception as e:
            print(f"[!] Error in browser session: {e}")
        finally:
            # Clean up
            if self._context is not None:
                try:
                    self._context.close()
                    try:
                        self._context.__exit__(None, None, None)
                    except Exception:
                        pass
                except Exception:
                    pass
                finally:
                    self._context = None


# Global session manager instance
session_manager = SessionManager()
