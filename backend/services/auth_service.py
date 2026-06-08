"""
Authentication Service for AI Lead Generator.

Handles JWT verification using Supabase JWKS (JSON), Public Keys (PEM), or Secrets (HS256).
"""

import logging
import json
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWK
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()

def get_key_from_jwks(kid: str) -> Any:
    """Helper to find and parse a specific key from the JWKS string."""
    if not settings.supabase_jwks:
        return None
    
    try:
        jwks = json.loads(settings.supabase_jwks)
        for key_dict in jwks.get("keys", []):
            if key_dict.get("kid") == kid:
                return PyJWK.from_dict(key_dict).key
        return None
    except Exception as e:
        logger.error(f"Error parsing JWKS: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verify the JWT token from Supabase Auth and return the user ID.
    Supports ES256 via local JWKS/Public Key and HS256 via Secret.
    """
    token = credentials.credentials
    
    try:
        # Detect algorithm and Key ID
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        kid = header.get("kid")
        
        # 1. Handle ES256 (Asymmetric)
        if alg == "ES256":
            # Priority 1: Try local JWKS (The data you just provided)
            key = get_key_from_jwks(kid) if kid else None
            
            # Priority 2: Fallback to manual public key PEM
            if not key:
                key = settings.supabase_jwt_public_key
            
            if not key:
                logger.error(f"Token uses ES256 but no key found for kid {kid}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Server configuration error: verification key missing"
                )
            
            payload = jwt.decode(
                token,
                key,
                algorithms=["ES256"],
                options={"verify_aud": False}
            )
            
        # 2. Handle HS256 (Symmetric)
        else:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: User ID missing"
            )
            
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidSignatureError:
        logger.error(f"Signature verification failed for alg {alg}. Check your keys in .env.")
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except Exception as e:
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
