"""Camoufox browser session management with threading."""
import asyncio
import os
import threading
import time
import tempfile
import shutil
from datetime import datetime
from typing import Any, Dict, Optional
import typing

from camoufox.addons import DefaultAddons
from playwright import async_api


class SessionManager:
    """Manages Camoufox browser sessions."""
    
    def __init__(self):
        self.active_session: Optional[Dict[str, Any]] = None
        self.browser_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._context = None
        self._temp_profile_dir: Optional[str] = None  # 临时配置目录（仅在非持久化时使用）
    
    def start_session(self, profile: Dict[str, Any], screen_width: Optional[int] = None, screen_height: Optional[int] = None) -> Dict[str, Any]:
        """
        Start a new Camoufox browser session.
        
        Args:
            profile: Profile dictionary with configuration
            screen_width: Optional screen width for fullscreen mode
            screen_height: Optional screen height for fullscreen mode
        
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
            args=(profile, screen_width, screen_height),
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
        
        # Context cleanup is handled by async context manager in _run_browser_async
        # Just clear the reference
        self._context = None
        
        # Clean up temporary profile directory if exists
        self._cleanup_temp_profile()
        
        # Clear session
        self.active_session = None
        self.browser_thread = None
    
    def get_session(self) -> Optional[Dict[str, Any]]:
        """Get current session status, auto-cleanup if session ended."""
        if self.active_session and not self.is_session_alive():
            # Thread ended, cleanup
            self.active_session = None
            self.browser_thread = None
            self._context = None
            
            # Clean up temporary profile directory if exists
            self._cleanup_temp_profile()
            
            return None
        return self.active_session.copy() if self.active_session else None
    
    def is_session_alive(self) -> bool:
        """Check if the browser session is still running."""
        if self.browser_thread is None or not self.browser_thread.is_alive():
            return False
        return True
    
    def _cleanup_temp_profile(self) -> None:
        """Clean up temporary profile directory if exists."""
        if self._temp_profile_dir and os.path.exists(self._temp_profile_dir):
            try:
                shutil.rmtree(self._temp_profile_dir)
                print(f"[*] Cleaned up temporary profile: {self._temp_profile_dir}")
                self._temp_profile_dir = None
            except Exception as e:
                print(f"[!] Failed to clean up temp profile: {e}")
    
    def _run_browser(self, profile: Dict[str, Any], screen_width: Optional[int] = None, screen_height: Optional[int] = None) -> None:
        """
        Run Camoufox browser in background thread.
        Entry point for threading - creates asyncio event loop.
        
        Args:
            profile: Profile configuration
            screen_width: Optional screen width for fullscreen mode
            screen_height: Optional screen height for fullscreen mode
        """
        try:
            asyncio.run(self._run_browser_async(profile, screen_width, screen_height))
        except Exception as e:
            print(f"[!] Error in browser session: {e}")
    
    async def _run_browser_async(self, profile: Dict[str, Any], screen_width: Optional[int] = None, screen_height: Optional[int] = None) -> None:
        """
        Async implementation of browser session management.
        Uses event listeners for reliable window close detection.
        
        Args:
            profile: Profile configuration
            screen_width: Optional screen width for fullscreen mode
            screen_height: Optional screen height for fullscreen mode
        """
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            print("[!] Camoufox not installed")
            return
        
        try:
            # Get viewport size - use screen dimensions if fullscreen and provided
            if profile.get('fullscreen') and screen_width and screen_height:
                width = screen_width
                height = screen_height
            else:
                width = profile.get('viewport_width', 1280)
                height = profile.get('viewport_height', 800)
            
            # Build Camoufox options
            opts: dict[str, Any]= {
                'headless': False,
                'window': (width + 2, height + 88),
            }
            
            # Persistent context - ALWAYS use it for Firefox/Camoufox to avoid window close issues
            # See playwright_firefox.md for details
            if profile.get('storage_enabled', False) and profile.get('persistent_dir'):
                # 用户启用了存储 - 使用用户指定的目录
                os.makedirs(profile['persistent_dir'], exist_ok=True)
                opts['persistent_context'] = True
                opts['user_data_dir'] = os.path.abspath(profile['persistent_dir'])
            else:
                # 用户禁用了存储 - 使用临时目录（会话结束后自动清理）
                # 这样可以确保返回 BrowserContext 类型，避免 Firefox 的主窗口关闭问题
                timestamp_ms = int(time.time() * 1000)
                self._temp_profile_dir = os.path.join(
                    tempfile.gettempdir(), 
                    f"tmp_camoufox_profile_{timestamp_ms}"
                )
                os.makedirs(self._temp_profile_dir, exist_ok=True)
                opts['persistent_context'] = True
                opts['user_data_dir'] = os.path.abspath(self._temp_profile_dir)
                print(f"[*] Using temporary profile: {self._temp_profile_dir}")
            
            # Proxy configuration - check enabled flag
            proxy_config = profile.get('proxy', {})
            if proxy_config.get('enabled') and proxy_config.get('host') and proxy_config.get('port'):
                protocol = proxy_config.get('protocol', 'socks5')
                proxy_dict = {
                    'server': f"{protocol}://{proxy_config['host']}:{proxy_config['port']}"
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
            async with AsyncCamoufox(**opts, i_know_what_im_doing=True,
                # exclude_addons=[DefaultAddons.UBO],
                config={
                    'disableTheming': True,
                    'showcursor': False,
            }) as context:
                if not isinstance(context, async_api.BrowserContext):
                    print(f"[!] Warning: Expected BrowserContext but got {type(context)} type")
                    return
                self._context = context
                
                # Get or create initial page
                page: async_api.Page
                if context.pages:
                    page = context.pages[0]
                else:
                    page = await context.new_page()
                
                # Set viewport
                try:
                    await page.set_viewport_size({'width': width, 'height': height})
                except Exception:
                    pass
                
                # Event-based window close detection
                close_event = asyncio.Event()
                # 监听 context 关闭
                def handle_close(bc: async_api.BrowserContext):
                    print("[*] BrowserContext closed")
                    close_event.set()
                context.on('close', handle_close)
                
                while not self._stop_flag.is_set():
                    try:
                        # Wait for close event with timeout to check _stop_flag
                        await asyncio.wait_for(close_event.wait(), timeout=0.5)
                        print("[*] Browser closed by user")
                        break  # Browser disconnected or all pages closed
                    except asyncio.TimeoutError:
                        continue  # Timeout, continue checking _stop_flag
                
                print("[*] Browser session ending")
        
        except Exception as e:
            print(f"[!] Error in async browser session: {e}")
        finally:
            # Cleanup is handled by async context manager
            self._context = None
            # Clean up temporary profile directory if exists
            self._cleanup_temp_profile()


# Global session manager instance
session_manager = SessionManager()
