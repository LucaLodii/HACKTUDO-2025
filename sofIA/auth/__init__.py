"""
Enterprise Authentication System for sofIA

Implements service account authentication, OAuth2/OpenID Connect integration,
and enterprise-grade security for commercial deployment.
"""

from .service_account import ServiceAccountManager, ServiceAccount
from .oauth2_provider import OAuth2Provider, OAuth2Token
from .auth_middleware import AuthenticationMiddleware
from .vertex_ai_auth import VertexAIAuthenticator

__all__ = [
    "ServiceAccountManager",
    "ServiceAccount",
    "OAuth2Provider",
    "OAuth2Token",
    "AuthenticationMiddleware",
    "VertexAIAuthenticator"
]