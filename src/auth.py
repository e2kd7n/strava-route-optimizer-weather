"""
Strava authentication module.

Handles OAuth 2.0 authentication flow and token management.
"""

import json
import logging
import webbrowser
from pathlib import Path
from typing import Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from stravalib.client import Client

logger = logging.getLogger(__name__)


class StravaAuthenticator:
    """Handles Strava OAuth authentication and token management."""
    
    def __init__(self, client_id: str, client_secret: str, 
                 credentials_path: str = "config/credentials.json"):
        """
        Initialize authenticator.
        
        Args:
            client_id: Strava API client ID
            client_secret: Strava API client secret
            credentials_path: Path to store credentials
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.credentials_path = Path(credentials_path)
        self.redirect_uri = "http://localhost:8000/authorized"
        
    def get_authorization_url(self) -> str:
        """
        Generate Strava OAuth authorization URL.
        
        Returns:
            Authorization URL string
        """
        client = Client()
        url = client.authorization_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=['activity:read_all', 'profile:read_all']
        )
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
        
        return {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }
    
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
        
        return {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }
    
    def save_tokens(self, tokens: Dict[str, any]) -> None:
        """
        Save tokens to file.
        
        Args:
            tokens: Dictionary containing tokens
        """
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.credentials_path, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        logger.info(f"Tokens saved to {self.credentials_path}")
    
    def load_tokens(self) -> Optional[Dict[str, any]]:
        """
        Load tokens from file.
        
        Returns:
            Dictionary containing tokens, or None if file doesn't exist
        """
        if not self.credentials_path.exists():
            return None
        
        with open(self.credentials_path, 'r') as f:
            tokens = json.load(f)
        
        return tokens
    
    def authenticate(self) -> Dict[str, any]:
        """
        Perform OAuth authentication flow.
        
        Returns:
            Dictionary containing access tokens
        """
        # Check if we have existing tokens
        tokens = self.load_tokens()
        if tokens:
            logger.info("Found existing tokens")
            # TODO: Check if token is expired and refresh if needed
            return tokens
        
        # Start OAuth flow
        logger.info("Starting OAuth authentication flow...")
        auth_url = self.get_authorization_url()
        
        # Open browser for authorization
        logger.info(f"Opening browser for authorization: {auth_url}")
        webbrowser.open(auth_url)
        
        # Start local server to receive callback
        code = self._wait_for_callback()
        
        # Exchange code for token
        logger.info("Exchanging authorization code for token...")
        tokens = self.exchange_code_for_token(code)
        
        # Save tokens
        self.save_tokens(tokens)
        
        logger.info("Authentication successful!")
        return tokens
    
    def _wait_for_callback(self) -> str:
        """
        Start local HTTP server and wait for OAuth callback.
        
        Returns:
            Authorization code from callback
        """
        code_container = {'code': None}
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse query parameters
                query = urlparse(self.path).query
                params = parse_qs(query)
                
                if 'code' in params:
                    code_container['code'] = params['code'][0]
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                        <html>
                        <body>
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to the application.</p>
                        </body>
                        </html>
                    """)
                else:
                    self.send_response(400)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # Suppress server logs
                pass
        
        # Start server
        server = HTTPServer(('localhost', 8000), CallbackHandler)
        logger.info("Waiting for authorization callback on http://localhost:8000...")
        
        # Handle one request
        server.handle_request()
        server.server_close()
        
        if code_container['code'] is None:
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
        
        client = Client(access_token=tokens['access_token'])
        return client


def get_authenticated_client(config) -> Client:
    """
    Get authenticated Strava client using configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        Authenticated stravalib Client
    """
    authenticator = StravaAuthenticator(
        client_id=config.get('strava.client_id'),
        client_secret=config.get('strava.client_secret')
    )
    
    return authenticator.get_authenticated_client()

# Made with Bob
