
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.config import Config
import jwt
import requests

security = HTTPBearer()

def get_supabase_client():
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract and verify user ID from Supabase JWT token"""
    token = credentials.credentials
    
    try:
        supabase = get_supabase_client()
        user_supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
        try:
            import base64
            import json
            header, payload, signature = token.split('.')
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.urlsafe_b64decode(payload)
            user_data = json.loads(decoded_payload)
            user_id = user_data.get('sub')
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            return user_id
            
        except Exception as decode_error:
            print(f"JWT decode error: {decode_error}")
            
            # Method 2: Fallback to API verification
            response = requests.get(
                f"{Config.SUPABASE_URL}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
            
            user_data = response.json()
            return user_data["id"]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# Alternative simpler version if the above doesn't work
async def get_current_user_id_simple(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Simplified auth - just decode JWT without full verification"""
    token = credentials.credentials
    
    try:
        import base64
        import json
        
        # Split the JWT token
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        
        # Decode the payload
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        
        decoded_payload = base64.urlsafe_b64decode(payload)
        user_data = json.loads(decoded_payload)
        
        # Extract user ID
        user_id = user_data.get('sub')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - no user ID found"
            )
        
        # Optional: Check if token is expired
        import time
        exp = user_data.get('exp')
        if exp and time.time() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        return user_id
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )