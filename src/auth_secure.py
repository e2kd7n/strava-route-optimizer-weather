"""
Secure Strava authentication module with enhanced security features.

Implements:
- Encrypted token storage
- OAuth CSRF protection (state parameter)
- Security audit logging
- Rate limiting on OAuth callback
- Secure file permissions
- Security headers

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.
"""

import json
import logging
import webbrowser
import sys
import os
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
from collections import defaultdict
from time import time as current_time

from stravalib.client import Client
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Security audit logger
security_logger = logging.getLogger('security_audit')
security_handler = None


def setup_security_logging():
    """Setup security audit logging."""
    global security_handler
    if security_handler is None:
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True, mode=0o700)
        
        security_handler = logging.FileHandler('logs/security_audit.log')
        security_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        # Prevent security logs from propagating to console
        security_logger.propagate = False

def log_security_event(event_type: str, details: dict):
    """Log security-relevant events."""
    setup_security_logging()
    security_logger.info(f"{event_type}: {json.dumps(details)}")


def validate_strava_credentials(client_id: str, client_secret: str) -> bool:
    """
    Validate that Strava API credentials are properly configured and functional.
    
    Args:
        client_id: Strava API client ID
        client_secret: Strava API client secret
        
    Returns:
        True if credentials are valid
        
    Raises:
        SystemExit: If credentials are invalid or missing
    """
    # Check if credentials are provided
    if not client_id or not client_secret:
        logger.error("=" * 70)
        logger.error("STRAVA API CREDENTIALS REQUIRED")
        logger.error("=" * 70)
        logger.error("This application requires valid Strava API credentials to run.")
        logger.error("")
        logger.error("To obtain credentials:")
        logger.error("1. Go to https://www.strava.com/settings/api")
        logger.error("2. Create a new application")
        logger.error("3. Add your Client ID and Client Secret to .env file")
        logger.error("")
        logger.error("See AUTHENTICATION_GUIDE.md for detailed instructions.")
        logger.error("=" * 70)
        log_security_event('AUTH_FAILED', {'reason': 'missing_credentials'})
        sys.exit(1)
    
    # Validate credential format (basic check)
    try:
        client_id_int = int(client_id)
        if client_id_int <= 0:
            raise ValueError("Invalid client ID")
    except (ValueError, TypeError):
        logger.error("=" * 70)
        logger.error("INVALID STRAVA CLIENT ID")
        logger.error("=" * 70)
        logger.error(f"The provided Client ID '{client_id}' is not valid.")
        logger.error("Client ID must be a positive integer.")
        logger.error("")
        logger.error("Please check your .env file and ensure:")
        logger.error("STRAVA_CLIENT_ID=your_actual_client_id")
        logger.error("=" * 70)
        log_security_event('AUTH_FAILED', {'reason': 'invalid_client_id'})
        sys.exit(1)
    
    if not isinstance(client_secret, str) or len(client_secret) < 20:
        logger.error("=" * 70)
        logger.error("INVALID STRAVA CLIENT SECRET")
        logger.error("=" * 70)
        logger.error("The provided Client Secret appears to be invalid.")
        logger.error("Client Secret should be a 40-character hexadecimal string.")
        logger.error("")
        logger.error("Please check your .env file and ensure:")
        logger.error("STRAVA_CLIENT_SECRET=your_actual_client_secret")
        logger.error("=" * 70)
        log_security_event('AUTH_FAILED', {'reason': 'invalid_client_secret'})
        sys.exit(1)
    
    logger.info("✓ Strava API credentials validated")
    log_security_event('CREDENTIALS_VALIDATED', {'timestamp': datetime.now(timezone.utc).isoformat()})
    return True


class SecureTokenStorage:
    """Handles encrypted storage of OAuth tokens."""
    
    def __init__(self, credentials_path: str):
        """
        Initialize secure token storage.
        
        Args:
            credentials_path: Path to store encrypted credentials
        """
        self.credentials_path = Path(credentials_path)
        
        # Get or generate encryption key
        key = os.getenv('TOKEN_ENCRYPTION_KEY')
        if not key:
            # Generate new key
            key = Fernet.generate_key()
            logger.warning("=" * 70)
            logger.warning("GENERATED NEW TOKEN ENCRYPTION KEY")
            logger.warning("=" * 70)
            logger.warning("A new encryption key has been generated for token storage.")
            logger.warning("To persist this key across sessions, add to your .env file:")
            logger.warning(f"TOKEN_ENCRYPTION_KEY={key.decode()}")
            logger.warning("=" * 70)
            log_security_event('ENCRYPTION_KEY_GENERATED', {'timestamp': datetime.now(timezone.utc).isoformat()})
        
        self.cipher = Fernet(key if isinstance(key, bytes) else key.encode())
    
    def save_tokens(self, tokens: Dict[str, any]) -> None:
        """
        Save tokens with encryption and secure permissions.
        
        Args:
            tokens: Dictionary containing tokens
        """
        # Create directory with restrictive permissions
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Encrypt token data
        token_json = json.dumps(tokens)
        encrypted = self.cipher.encrypt(token_json.encode())
        
        # Write encrypted data
        with open(self.credentials_path, 'wb') as f:
            f.write(encrypted)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(self.credentials_path, 0o600)
        
        logger.info(f"✓ Tokens saved securely to {self.credentials_path}")
        log_security_event('TOKENS_SAVED', {
            'path': str(self.credentials_path),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def load_tokens(self) -> Optional[Dict[str, any]]:
        """
        Load and decrypt tokens.
        
        Returns:
            Dictionary containing tokens, or None if file doesn't exist
        """
        if not self.credentials_path.exists():
            return None
        
        try:
            with open(self.credentials_path, 'rb') as f:
                encrypted = f.read()
            
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted)
            tokens = json.loads(decrypted.decode())
            
            log_security_event('TOKENS_LOADED', {
                'path': str(self.credentials_path),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            log_security_event('TOKENS_LOAD_FAILED', {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return None


class RateLimitedCallbackHandler(BaseHTTPRequestHandler):
    """HTTP callback handler with rate limiting and security features."""
    
    # Class-level rate limit tracking
    request_counts = defaultdict(list)
    MAX_REQUESTS = 10
    TIME_WINDOW = 60  # seconds
    
    # Will be set by server
    expected_state = None
    code_container = None
    
    def do_GET(self):
        """Handle GET request with rate limiting and validation."""
        # Get client IP
        client_ip = self.client_address[0]
        
        # Check rate limit
        now = current_time()
        self.request_counts[client_ip] = [
            t for t in self.request_counts[client_ip]
            if now - t < self.TIME_WINDOW
        ]
        
        if len(self.request_counts[client_ip]) >= self.MAX_REQUESTS:
            self.send_response(429)  # Too Many Requests
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Rate limit exceeded</h1>")
            log_security_event('RATE_LIMIT_EXCEEDED', {
                'client_ip': client_ip,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return
        
        self.request_counts[client_ip].append(now)
        
        # Parse query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        # Validate state parameter (CSRF protection)
        if 'state' not in params:
            self.send_response(400)
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Error: Missing state parameter</h1>")
            log_security_event('OAUTH_CALLBACK_FAILED', {
                'reason': 'missing_state',
                'client_ip': client_ip,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return
        
        received_state = params['state'][0]
        if received_state != self.expected_state:
            self.send_response(403)
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Error: Invalid state parameter (CSRF detected)</h1>")
            log_security_event('CSRF_ATTEMPT_DETECTED', {
                'client_ip': client_ip,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return
        
        # State validated, check for authorization code
        if 'code' in params:
            self.code_container['code'] = params['code'][0]
            self.code_container['state'] = received_state
            
            # Send success response with security headers
            self.send_response(200)
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head>
                    <title>Authorization Successful</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #4CAF50; }
                    </style>
                </head>
                <body>
                    <h1>&#10004; Authorization Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
                </html>
            """)
            log_security_event('OAUTH_CALLBACK_SUCCESS', {
                'client_ip': client_ip,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        else:
            self.send_response(400)
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Error: Missing authorization code</h1>")
            log_security_event('OAUTH_CALLBACK_FAILED', {
                'reason': 'missing_code',
                'client_ip': client_ip,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    def _send_security_headers(self):
        """Send security headers with HTTP response."""
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'")
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-XSS-Protection', '1; mode=block')
    
    def log_message(self, format, *args):
        """Suppress default server logs (we use security audit log instead)."""
        pass


class SecureStravaAuthenticator:
    """Handles Strava OAuth authentication with enhanced security."""
    
    def __init__(self, client_id: str, client_secret: str, 
                 credentials_path: str = "config/credentials.json"):
        """
        Initialize secure authenticator.
        
        Args:
            client_id: Strava API client ID
            client_secret: Strava API client secret
            credentials_path: Path to store encrypted credentials
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_storage = SecureTokenStorage(credentials_path)
        self.redirect_uri = "http://localhost:8000/authorized"
        self.state = None  # CSRF token
        
        # Setup security logging
        setup_security_logging()
    
    def get_authorization_url(self) -> str:
        """
        Generate Strava OAuth authorization URL with CSRF protection.
        
        Returns:
            Authorization URL string
        """
        client = Client()
        
        # Generate cryptographically secure state token
        self.state = secrets.token_urlsafe(32)
        
        url = client.authorization_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=['activity:read_all', 'profile:read_all'],
            state=self.state  # CSRF protection
        )
        
        log_security_event('AUTH_URL_GENERATED', {
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        return url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dictionary containing access token and refresh token
        """
        client = Client()
        token_response = client.exchange_code_for_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code
        )
        
        tokens = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }
        
        log_security_event('TOKEN_EXCHANGED', {
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        return tokens
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh expired access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dictionary containing new access token
        """
        client = Client()
        token_response = client.refresh_access_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=refresh_token
        )
        
        tokens = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }
        
        log_security_event('TOKEN_REFRESHED', {
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        return tokens
    
    def save_tokens(self, tokens: Dict[str, any]) -> None:
        """Save tokens using secure storage."""
        self.token_storage.save_tokens(tokens)
    
    def load_tokens(self) -> Optional[Dict[str, any]]:
        """Load tokens from secure storage."""
        return self.token_storage.load_tokens()
    
    def authenticate(self) -> Dict[str, any]:
        """
        Perform OAuth authentication flow with security enhancements.
        
        Returns:
            Dictionary containing access tokens
        """
        log_security_event('AUTH_START', {'timestamp': datetime.now(timezone.utc).isoformat()})
        
        # Check if we have existing tokens
        tokens = self.load_tokens()
        if tokens:
            logger.info("Found existing tokens")
            # Check if token needs refresh
            import time
            if tokens['expires_at'] < time.time():
                logger.info("Access token expired, refreshing...")
                tokens = self.refresh_access_token(tokens['refresh_token'])
                self.save_tokens(tokens)
            log_security_event('AUTH_SUCCESS', {
                'method': 'existing_tokens',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return tokens
        
        # Start OAuth flow
        logger.info("Starting OAuth authentication flow...")
        auth_url = self.get_authorization_url()
        
        # Open browser for authorization
        logger.info(f"Opening browser for authorization...")
        webbrowser.open(auth_url)
        
        # Start local server to receive callback
        code = self._wait_for_callback()
        
        # Exchange code for token
        logger.info("Exchanging authorization code for token...")
        tokens = self.exchange_code_for_token(code)
        
        # Save tokens securely
        self.save_tokens(tokens)
        
        logger.info("✓ Authentication successful!")
        log_security_event('AUTH_SUCCESS', {
            'method': 'oauth_flow',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        return tokens
    
    def _wait_for_callback(self) -> str:
        """
        Start local HTTP server and wait for OAuth callback with security features.
        
        Returns:
            Authorization code from callback
        """
        code_container = {'code': None, 'state': None}
        
        # Configure handler with state and code container
        RateLimitedCallbackHandler.expected_state = self.state
        RateLimitedCallbackHandler.code_container = code_container
        
        # Start server
        server = HTTPServer(('localhost', 8000), RateLimitedCallbackHandler)
        logger.info("Waiting for authorization callback on http://localhost:8000...")
        log_security_event('CALLBACK_SERVER_STARTED', {
            'port': 8000,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Handle one request
        server.handle_request()
        server.server_close()
        
        if code_container['code'] is None:
            log_security_event('CALLBACK_FAILED', {
                'reason': 'no_code_received',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            raise ValueError("Failed to receive authorization code")
        
        return code_container['code']
    
    def get_authenticated_client(self) -> Client:
        """
        Get authenticated Strava client.
        
        Returns:
            Authenticated stravalib Client
        """
        tokens = self.load_tokens()
        
        if tokens is None:
            raise ValueError("No tokens found. Please authenticate first.")
        
        # Check if token needs refresh
        import time
        if tokens['expires_at'] < time.time():
            logger.info("Access token expired, refreshing...")
            tokens = self.refresh_access_token(tokens['refresh_token'])
            self.save_tokens(tokens)
        
        # Create client with full token info for auto-refresh feature
        # This eliminates warnings about missing refresh_token and token_expires
        client = Client(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token']
        )
        # Set token expiration time as an attribute (not a constructor parameter)
        client.token_expires_at = tokens['expires_at']
        return client


def get_authenticated_client(config) -> Client:
    """
    Get authenticated Strava client using configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        Authenticated stravalib Client
    """
    authenticator = SecureStravaAuthenticator(
        client_id=config.get('strava.client_id'),
        client_secret=config.get('strava.client_secret')
    )
    
    return authenticator.get_authenticated_client()


# Made with Bob - Enhanced Security Edition