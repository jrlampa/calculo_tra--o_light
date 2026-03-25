# Relatório Técnico - Security Engineer

## 📊 Análise de Segurança

### Stack de Segurança Atual
- **Authentication**: Session-based (✅ presente)
- **Authorization**: Role-based (admin/user) (✅ presente)
- **Data Protection**: HTTPS (parcial)
- **Input Validation**: Básica (❌ insuficiente)
- **Security Headers**: Ausentes (❌)
- **Dependency Scanning**: Ausente (❌)

### 🏗️ Arquitetura de Segurança

```
Security Implementations:
├── api/auth.py (JWT + Sessions)
├── CORS middleware (básico)
├── Environment variables (.env)
├── Supabase RLS (Row Level Security)
└── Basic input validation (Pydantic)

Security Gaps:
├── No rate limiting
├── No security headers
├── No audit logging
├── No vulnerability scanning
├── No encryption at rest
└── No security monitoring
```

## ⚠️ Problemas Críticos Identificados

### 🚨 Crítico (Impacto Alto/Esf. Baixo)

#### 1. **Rate Limiting Ausente**
```python
# PROBLEMA: Sem rate limiting
# API vulnerável a DoS/Brute force
# Sem proteção contra abuso
# Risk: Disponibilidade comprometida
```

**Solução Imediata**: Rate Limiting Robusto
```python
# middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from fastapi import Request, HTTPException
import time

# Redis client for distributed rate limiting
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Custom key generator for different endpoints
def get_endpoint_key(request: Request) -> str:
    endpoint = f"{request.method}:{request.url.path}"
    client_ip = get_remote_address(request)
    return f"rate_limit:{endpoint}:{client_ip}"

# Initialize limiter
limiter = Limiter(
    key_func=get_endpoint_key,
    storage_uri="redis://localhost:6379",
    default_limits=["1000/hour", "100/minute"]
)

# Custom rate limits for sensitive endpoints
class RateLimitConfig:
    LOGIN = "5/minute"
    REGISTER = "3/minute" 
    CALCULATE = "60/minute"
    PROJECT_CREATE = "10/minute"
    ADMIN_ENDPOINTS = "30/minute"

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Check endpoint-specific limits
    endpoint = f"{request.method}:{request.url.path}"
    
    if endpoint in ["POST:/api/auth/login"]:
        await check_rate_limit(request, RateLimitConfig.LOGIN)
    elif endpoint in ["POST:/api/calcular"]:
        await check_rate_limit(request, RateLimitConfig.CALCULATE)
    elif endpoint in ["POST:/api/projetos"]:
        await check_rate_limit(request, RateLimitConfig.PROJECT_CREATE)
    
    response = await call_next(request)
    return response

async def check_rate_limit(request: Request, limit: str):
    client_ip = get_remote_address(request)
    key = f"rate_limit:{client_ip}:{request.url.path}"
    
    current = redis_client.get(key)
    if current is None:
        redis_client.setex(key, 60, 1)
        return
    
    count = int(current)
    max_requests, period = parse_limit(limit)
    
    if count >= max_requests:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(period)}
        )
    
    redis_client.incr(key)

def parse_limit(limit_str: str) -> tuple[int, int]:
    """Parse '5/minute' -> (5, 60)"""
    count, period = limit_str.split('/')
    period_map = {'second': 1, 'minute': 60, 'hour': 3600}
    return int(count), period_map.get(period, 60)

# Exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
        headers={"Retry-After": "60"}
    )
```

#### 2. **Security Headers Ausentes**
```python
# PROBLEMA: Sem security headers
# Vulnerável a XSS, clickjacking, MITM
# Sem proteção de conteúdo
# Risk: Múltiplas vulnerabilidades web
```

**Solução**: Security Headers Middleware
```python
# middleware/security_headers.py
from fastapi import Response
from fastapi.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.supabase.co; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Strict Transport Security (HTTPS only)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy
        
        return response

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
```

#### 3. **Input Validation Insuficiente**
```python
# PROBLEMA: Validação básica apenas
# Vulnerável a injection attacks
# Sem sanitização adequada
# Risk: SQL injection, XSS, NoSQL injection
```

**Solução**: Input Validation Robusta
```python
# security/validation.py
import re
import html
import bleach
from typing import Any, Dict, List
from pydantic import validator, Field
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Length check
        if len(value) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")
        
        # Remove potential dangerous characters
        sanitized = html.escape(value.strip())
        
        # Additional sanitization for specific contexts
        dangerous_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',              # JavaScript URLs
            r'on\w+\s*=',               # Event handlers
            r'expression\s*\(',         # CSS expressions
            r'@import',                 # CSS imports
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                logger.warning(f"Potentially dangerous input detected: {value[:50]}...")
                raise ValueError("Invalid characters detected")
        
        return sanitized
    
    @staticmethod
    def validate_numeric_range(value: float, min_val: float = None, max_val: float = None) -> float:
        """Validate numeric input within range"""
        if not isinstance(value, (int, float)):
            raise ValueError("Input must be numeric")
        
        if min_val is not None and value < min_val:
            raise ValueError(f"Value must be >= {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValueError(f"Value must be <= {max_val}")
        
        return value
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
        """Validate geographic coordinates"""
        lat = SecurityValidator.validate_numeric_range(lat, -90, 90)
        lon = SecurityValidator.validate_numeric_range(lon, -180, 180)
        return lat, lon
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return email.lower().strip()
    
    @staticmethod
    def validate_project_id(project_id: str) -> str:
        """Validate project ID format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', project_id):
            raise ValueError("Invalid project ID format")
        return project_id

# Enhanced Pydantic models with security validation
from pydantic import BaseModel

class SecureProjetoInput(BaseModel):
    orgao: str = Field(..., min_length=2, max_length=100)
    ns: str = Field(..., min_length=1, max_length=50)
    nome: str = Field(..., min_length=2, max_length=200)
    endereco: str = Field(..., max_length=500)
    estudado_por: str = Field(..., min_length=2, max_length=100)
    matricula: str = Field(..., min_length=1, max_length=20)
    
    @validator('orgao', 'nome', 'endereco', 'estudado_por')
    def sanitize_strings(cls, v):
        return SecurityValidator.sanitize_string(v)
    
    @validator('ns', 'matricula')
    def sanitize_identifiers(cls, v):
        return SecurityValidator.sanitize_string(v, max_length=50)

class SecureCalculoInput(BaseModel):
    mt1: List[Dict[str, Any]]
    mt2: List[Dict[str, Any]]
    bt: List[Dict[str, Any]]
    btz: List[Dict[str, Any]]
    ral: List[Dict[str, Any]]
    
    @validator('mt1', 'mt2', 'bt', 'btz', 'ral')
    def validate_travessias(cls, v):
        if len(v) > 10:  # Reasonable limit
            raise ValueError("Too many travessias")
        
        for travessia in v:
            # Validate each field
            if 'vao' in travessia:
                travessia['vao'] = SecurityValidator.validate_numeric_range(
                    travessia['vao'], 0.1, 1000
                )
            
            if 'flecha' in travessia:
                travessia['flecha'] = SecurityValidator.validate_numeric_range(
                    travessia['flecha'], 0, 50
                )
            
            if 'angulo' in travessia:
                travessia['angulo'] = SecurityValidator.validate_numeric_range(
                    travessia['angulo'], 0, 360
                )
        
        return v
```

### 🔴 Alto (Impacto Alto/Esf. Médio)

#### 4. **Logging e Auditoria Ausentes**
```python
# PROBLEMA: Sem audit trail
# Sem logging de segurança
# Impossível investigar incidentes
# Risk: Falha de compliance e forensics
```

**Solução**: Security Logging System
```python
# security/audit_logger.py
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request
from pythonjsonlogger import jsonlogger

# Structured logger for security events
security_logger = logging.getLogger('security')
security_handler = logging.StreamHandler()
security_handler.setFormatter(jsonlogger.JsonFormatter())
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

class SecurityEvent:
    """Security event logging"""
    
    @staticmethod
    def log_login_attempt(request: Request, email: str, success: bool, ip: str, user_agent: str):
        event = {
            'event_type': 'login_attempt',
            'timestamp': datetime.utcnow().isoformat(),
            'email': email,
            'success': success,
            'ip_address': ip,
            'user_agent': user_agent,
            'endpoint': str(request.url.path),
            'method': request.method
        }
        security_logger.info(json.dumps(event))
    
    @staticmethod
    def log_permission_denied(request: Request, user_id: str, resource: str, action: str):
        event = {
            'event_type': 'permission_denied',
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'ip_address': request.client.host,
            'endpoint': str(request.url.path),
            'method': request.method
        }
        security_logger.warning(json.dumps(event))
    
    @staticmethod
    def log_suspicious_activity(request: Request, reason: str, details: Dict[str, Any]):
        event = {
            'event_type': 'suspicious_activity',
            'timestamp': datetime.utcnow().isoformat(),
            'reason': reason,
            'details': details,
            'ip_address': request.client.host,
            'user_agent': request.headers.get('user-agent'),
            'endpoint': str(request.url.path),
            'method': request.method
        }
        security_logger.error(json.dumps(event))
    
    @staticmethod
    def log_data_access(request: Request, user_id: str, resource_type: str, resource_id: str):
        event = {
            'event_type': 'data_access',
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': request.client.host,
            'endpoint': str(request.url.path),
            'method': request.method
        }
        security_logger.info(json.dumps(event))

# Audit middleware
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    # Log API access
    if request.url.path.startswith('/api/'):
        SecurityEvent.log_data_access(
            request=request,
            user_id=getattr(request.state, 'current_user_id', 'anonymous'),
            resource_type='api_endpoint',
            resource_id=str(request.url.path)
        )
    
    return response

# Usage in endpoints
@app.post("/api/auth/login")
async def login(request: Request, credentials: LoginCredentials):
    ip = request.client.host
    user_agent = request.headers.get('user-agent', '')
    
    try:
        user = await authenticate_user(credentials.email, credentials.password)
        SecurityEvent.log_login_attempt(request, credentials.email, True, ip, user_agent)
        return {"token": create_token(user)}
    except Exception as e:
        SecurityEvent.log_login_attempt(request, credentials.email, False, ip, user_agent)
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

#### 5. **Encryption at Rest Ausente**
```python
# PROBLEMA: Dados sensíveis não criptografados
# Sem encryption de campos críticos
# Risk: Exposição de dados em breach
```

**Solução**: Field-Level Encryption
```python
# security/encryption.py
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import json
from typing import Any, Dict

class FieldEncryption:
    """Field-level encryption for sensitive data"""
    
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet cipher from master key"""
        salt = b'stable_salt_for_consistency'  # In production, use random salt per encryption
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key)
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a single field value"""
        if not value:
            return value
        
        encrypted = self.fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a single field value"""
        if not encrypted_value:
            return encrypted_value
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Invalid encrypted data")
    
    def encrypt_dict_fields(self, data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt_field(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict_fields(self, data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_field(decrypted_data[field])
                except ValueError:
                    # Field might not be encrypted, keep original
                    pass
        
        return decrypted_data

# Initialize encryption
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())
field_encryptor = FieldEncryption(ENCRYPTION_KEY)

# Sensitive fields to encrypt
SENSITIVE_FIELDS = [
    'email',
    'matricula',
    'estudado_por',
    'endereco'
]

# Usage in repositories
class SecureProjetoRepository:
    async def save_projeto(self, projeto_data: Dict[str, Any]) -> str:
        # Encrypt sensitive fields before saving
        encrypted_data = field_encryptor.encrypt_dict_fields(projeto_data, SENSITIVE_FIELDS)
        
        # Save to database
        projeto_id = await self.db.insert('projetos', encrypted_data)
        
        # Log the encryption
        SecurityEvent.log_data_access(
            request=None,  # Background operation
            user_id='system',
            resource_type='projeto',
            resource_id=projeto_id
        )
        
        return projeto_id
    
    async def get_projeto(self, projeto_id: str) -> Dict[str, Any]:
        # Get from database
        projeto_data = await self.db.get('projetos', projeto_id)
        
        if projeto_data:
            # Decrypt sensitive fields
            decrypted_data = field_encryptor.decrypt_dict_fields(projeto_data, SENSITIVE_FIELDS)
            return decrypted_data
        
        return None
```

#### 6. **Session Security Fraca**
```python
# PROBLEMA: Session management básico
# Sem session rotation
# Sem invalidação adequada
# Risk: Session hijacking
```

**Solução**: Secure Session Management
```python
# security/session_manager.py
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
import redis

class SecureSessionManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.session_timeout = 3600  # 1 hour
        self.absolute_timeout = 86400  # 24 hours
    
    def create_session(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """Create secure session with rotation"""
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        
        # Session data
        session_data = {
            'user_id': user_id,
            'user_data': user_data,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'ip_address': user_data.get('ip_address'),
            'user_agent': user_data.get('user_agent'),
            'csrf_token': secrets.token_urlsafe(16)
        }
        
        # Store session with TTL
        self.redis.setex(
            f"session:{session_id}",
            self.session_timeout,
            json.dumps(session_data)
        )
        
        # Track user sessions for invalidation
        self.redis.sadd(f"user_sessions:{user_id}", session_id)
        
        return session_token
    
    def validate_session(self, session_token: str, request_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and rotate session"""
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        
        session_data = self.redis.get(f"session:{session_id}")
        if not session_data:
            return None
        
        try:
            session = json.loads(session_data)
            
            # Check session age
            created_at = datetime.fromisoformat(session['created_at'])
            if datetime.utcnow() - created_at > timedelta(seconds=self.absolute_timeout):
                self.invalidate_session(session_token)
                return None
            
            # Check for session fixation
            current_ip = request_context.get('ip_address')
            current_ua = request_context.get('user_agent')
            
            if (session['ip_address'] != current_ip or 
                session['user_agent'] != current_ua):
                SecurityEvent.log_suspicious_activity(
                    request=None,
                    reason="Session context mismatch",
                    details={
                        'session_id': session_id,
                        'expected_ip': session['ip_address'],
                        'actual_ip': current_ip,
                        'expected_ua': session['user_agent'],
                        'actual_ua': current_ua
                    }
                )
                self.invalidate_session(session_token)
                return None
            
            # Update last activity and rotate session
            session['last_activity'] = datetime.utcnow().isoformat()
            self.redis.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(session)
            )
            
            return session
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    def invalidate_session(self, session_token: str):
        """Invalidate specific session"""
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        
        session_data = self.redis.get(f"session:{session_id}")
        if session_data:
            try:
                session = json.loads(session_data)
                user_id = session['user_id']
                
                # Remove from user sessions
                self.redis.srem(f"user_sessions:{user_id}", session_id)
                
                # Delete session
                self.redis.delete(f"session:{session_id}")
                
            except (json.JSONDecodeError, KeyError):
                pass
    
    def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        session_ids = self.redis.smembers(f"user_sessions:{user_id}")
        
        for session_id in session_ids:
            self.redis.delete(f"session:{session_id}")
        
        self.redis.delete(f"user_sessions:{user_id}")
    
    def rotate_session(self, session_token: str, request_context: Dict[str, Any]) -> Optional[str]:
        """Rotate session token"""
        session = self.validate_session(session_token, request_context)
        if not session:
            return None
        
        # Invalidate old session
        self.invalidate_session(session_token)
        
        # Create new session
        return self.create_session(session['user_id'], {
            'ip_address': request_context.get('ip_address'),
            'user_agent': request_context.get('user_agent')
        })
```

### 🟡 Médio (Impacto Médio/Esf. Baixo)

#### 7. **Dependency Vulnerabilities**
```python
# PROBLEMA: Sem vulnerability scanning
# Dependencies desatualizadas
# Risk: Vulnerabilidades conhecidas
```

**Solução**: Automated Security Scanning
```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  push:
    branches: [main, dev]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          vuln-type: 'os,library'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Python dependency check
        run: |
          pip install safety
          safety check --json --output safety-report.json || true
      
      - name: Node.js dependency check
        run: |
          npm audit --audit-level=high --json > npm-audit.json || true
      
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            trivy-results.sarif
            safety-report.json
            npm-audit.json

  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker images
        run: |
          docker build -t calculo-tracao-api -f python/Dockerfile.api .
          docker build -t calculo-tracao-web -f Dockerfile.web .
      
      - name: Run Trivy on containers
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'calculo-tracao-api,calculo-tracao-web'
          format: 'sarif'
          output: 'container-trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload container scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'container-trivy-results.sarif'
```

#### 8. **Security Monitoring**
```python
# PROBLEMA: Sem monitoring de segurança
# Sem alertas de incidentes
# Risk: Incidentes não detectados
```

**Solução**: Security Monitoring
```python
# security/monitoring.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class SecurityAlert:
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    details: Dict[str, Any]
    timestamp: datetime

class SecurityMonitor:
    def __init__(self):
        self.alerts = []
        self.thresholds = {
            'failed_logins_per_minute': 10,
            'failed_logins_per_hour': 100,
            'suspicious_requests_per_minute': 50,
            'unusual_access_patterns': True
        }
    
    async def monitor_failed_logins(self):
        """Monitor for brute force attacks"""
        while True:
            # Count failed logins in last minute
            failed_count = await self.count_recent_events('login_attempt', success=False, minutes=1)
            
            if failed_count > self.thresholds['failed_logins_per_minute']:
                alert = SecurityAlert(
                    level='HIGH',
                    message='Potential brute force attack detected',
                    details={'failed_logins_per_minute': failed_count},
                    timestamp=datetime.utcnow()
                )
                await self.handle_alert(alert)
            
            await asyncio.sleep(60)  # Check every minute
    
    async def monitor_suspicious_requests(self):
        """Monitor for suspicious request patterns"""
        while True:
            # Check for unusual request patterns
            suspicious_count = await self.count_suspicious_requests(minutes=5)
            
            if suspicious_count > self.thresholds['suspicious_requests_per_minute']:
                alert = SecurityAlert(
                    level='MEDIUM',
                    message='Unusual request pattern detected',
                    details={'suspicious_requests': suspicious_count},
                    timestamp=datetime.utcnow()
                )
                await self.handle_alert(alert)
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def handle_alert(self, alert: SecurityAlert):
        """Handle security alerts"""
        self.alerts.append(alert)
        
        # Log alert
        logger.warning(f"Security Alert [{alert.level}]: {alert.message}")
        
        # Send notifications based on severity
        if alert.level in ['HIGH', 'CRITICAL']:
            await self.send_immediate_notification(alert)
        
        # Implement automatic response for critical alerts
        if alert.level == 'CRITICAL':
            await self.implement_auto_response(alert)
    
    async def send_immediate_notification(self, alert: SecurityAlert):
        """Send immediate notification for high-severity alerts"""
        # Integration with notification system (email, Slack, etc.)
        notification_data = {
            'alert_level': alert.level,
            'message': alert.message,
            'details': alert.details,
            'timestamp': alert.timestamp.isoformat()
        }
        
        # Send to security team
        await self.notify_security_team(notification_data)
    
    async def implement_auto_response(self, alert: SecurityAlert):
        """Implement automatic response for critical alerts"""
        if 'brute force' in alert.message.lower():
            # Block offending IPs temporarily
            await self.block_suspicious_ips(alert.details.get('ips', []))
        
        if 'data breach' in alert.message.lower():
            # Invalidate all sessions
            await self.invalidate_all_sessions()
    
    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate daily security report"""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        report = {
            'report_date': yesterday.date().isoformat(),
            'total_alerts': len(self.alerts),
            'alerts_by_level': self._count_alerts_by_level(),
            'top_threats': self._get_top_threats(),
            'blocked_ips': await self.get_blocked_ips_count(),
            'security_metrics': await self.get_security_metrics()
        }
        
        return report

# Initialize monitoring
security_monitor = SecurityMonitor()

# Start monitoring tasks
@app.on_event("startup")
async def start_security_monitoring():
    asyncio.create_task(security_monitor.monitor_failed_logins())
    asyncio.create_task(security_monitor.monitor_suspicious_requests())
```

## 🎯 Security Best Practices

### 1. **Environment Security**
```bash
# .env.example with security notes
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# ⚠️  Use strong passwords and SSL connections

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
# ⚠️  Use cryptographically secure random keys
SESSION_TTL_SECONDS=3600

# Encryption Key
ENCRYPTION_KEY=your-encryption-key-32-chars-min
# ⚠️  Store encryption keys securely (HSM, AWS KMS, etc.)

# CORS Configuration
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
# ⚠️  Be specific about allowed origins in production

# Redis Configuration
REDIS_URL=redis://localhost:6379
# ⚠️  Use Redis AUTH and TLS in production
```

### 2. **API Security Checklist**
```python
# security/checklist.py
class SecurityChecklist:
    """
    Security Implementation Checklist:
    
    ✅ Authentication & Authorization
    ✅ Input Validation & Sanitization  
    ✅ Rate Limiting
    ✅ Security Headers
    ✅ HTTPS Enforcement
    ✅ Session Management
    ✅ Encryption at Rest
    ✅ Audit Logging
    ✅ Error Handling
    ✅ Dependency Security
    ✅ Environment Security
    ✅ Monitoring & Alerting
    """
    
    @staticmethod
    async def run_security_checks():
        checks = [
            SecurityChecklist.check_authentication,
            SecurityChecklist.check_authorization,
            SecurityChecklist.check_input_validation,
            SecurityChecklist.check_rate_limiting,
            SecurityChecklist.check_security_headers,
            SecurityChecklist.check_encryption,
            SecurityChecklist.check_logging,
            SecurityChecklist.check_dependencies
        ]
        
        results = []
        for check in checks:
            try:
                result = await check()
                results.append(result)
            except Exception as e:
                results.append({'check': check.__name__, 'status': 'FAILED', 'error': str(e)})
        
        return results
```

## 🔧 Plano de Implementação Security

### Sprint 1 (Crítico)
1. Implementar rate limiting
2. Adicionar security headers
3. Fortalecer input validation

### Sprint 2 (Alto)
1. Implementar audit logging
2. Adicionar field encryption
3. Melhorar session management

### Sprint 3 (Médio)
1. Configurar dependency scanning
2. Implementar security monitoring
3. Adicionar automated responses

## 🚀 Recomendações Finais

### Imediatas
- **Prioridade 1**: Rate limiting
- **Prioridade 2**: Security headers
- **Investimento**: 30-40 horas

### Longo Prazo
- **Zero Trust Architecture**
- **Advanced threat detection**
- **Security automation**

---

**Status**: 🟡 **Requer Atenção Crítica**  
**Prioridade**: Altíssima  
**Investimento Estimado**: 40-60 horas  
**ROI Esperado**: 10x (proteção + compliance)
