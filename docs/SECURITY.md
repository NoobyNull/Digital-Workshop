# Security Guidelines

This document outlines security practices and guidelines for the Digital Workshop project.

## Overview

Digital Workshop is a local desktop application. Security focuses on:
- Protecting user data and projects
- Preventing malicious file imports
- Secure credential management
- Secure temporary file handling

## Security Modules

### 1. Path Validator (`src/core/security/path_validator.py`)

Prevents directory traversal attacks and validates file paths.

**Usage**:
```python
from src.core.security import PathValidator

validator = PathValidator(base_directory="/projects")
if validator.validate_path("../../../etc/passwd"):
    # Path is safe
    pass
```

**Features**:
- Prevents directory traversal (`../` attacks)
- Validates file extensions
- Blocks system files (.exe, .dll, .sys, etc.)

### 2. Credentials Manager (`src/core/security/credentials_manager.py`)

Manages API keys and credentials using environment variables.

**Usage**:
```python
from src.core.security import CredentialsManager

creds = CredentialsManager()
api_key = creds.get_credential("api_key")
```

**Best Practices**:
- Never store credentials in code
- Use environment variables (DW_* prefix)
- Load from `.env` file in development
- Use system credential stores in production

### 3. Temporary File Manager (`src/core/security/temp_file_manager.py`)

Securely manages temporary files with automatic cleanup.

**Usage**:
```python
from src.core.security import TempFileManager

temp_mgr = TempFileManager()
with temp_mgr.temporary_file(suffix=".tmp") as temp_path:
    # Use temporary file
    # Automatically cleaned up after use
    pass
```

**Features**:
- Automatic cleanup on exit
- Context manager support
- Prevents temp file leaks

### 4. Data Encryptor (`src/core/security/data_encryptor.py`)

Encrypts sensitive project data using Fernet symmetric encryption.

**Usage**:
```python
from src.core.security import DataEncryptor

encryptor = DataEncryptor()
key = encryptor.generate_key()
encrypted = encryptor.encrypt_data("sensitive data", key)
decrypted = encryptor.decrypt_data(encrypted, key)
```

**Features**:
- Fernet symmetric encryption
- File-level encryption support
- Secure key generation

### 5. Security Event Logger (`src/core/security/security_event_logger.py`)

Logs security-related events for audit trails.

**Usage**:
```python
from src.core.security import SecurityEventLogger, SecurityEventType

logger = SecurityEventLogger()
logger.log_event(
    SecurityEventType.PATH_VALIDATION_FAILED,
    "Invalid path attempted",
    {"path": "/etc/passwd"}
)
```

## File Import Security

When importing files:

1. **Path Validation**: All paths are validated to prevent directory traversal
2. **File Type Checking**: Only allowed file types are imported
3. **System File Blocking**: System files (.exe, .dll, etc.) are blocked
4. **Security Logging**: All security events are logged

**Blocked File Types**:
- `.exe`, `.dll`, `.sys` - Executables
- `.bat`, `.cmd`, `.ps1` - Scripts
- `.ini`, `.inf`, `.com` - Configuration/System
- `.msi` - Installers

## Credential Management

### Development

1. Create `.env` file in project root:
```
DW_API_KEY=your_api_key_here
DW_DATABASE_URL=your_db_url_here
```

2. Load credentials:
```python
from src.core.security import CredentialsManager

creds = CredentialsManager()
creds.load_credentials_from_env_file(".env")
```

### Production

1. Use system environment variables
2. Never commit `.env` files
3. Use secure credential stores (e.g., AWS Secrets Manager)

## Dependency Security

Check for vulnerable dependencies:

```bash
python -m pip_audit
```

Audit report: `docs/reports/dependency_audit.json`

## Code Security Checks

Automated security scanning with Bandit:

```bash
bandit -r src
```

## Security Best Practices

1. **Never log sensitive data**
   - Use `CredentialsManager.mask_credential()` for logging
   - Avoid logging passwords, API keys, tokens

2. **Validate all user input**
   - Use `PathValidator` for file paths
   - Validate file types and sizes

3. **Use context managers**
   - Use `TempFileManager` for temporary files
   - Ensures cleanup even on errors

4. **Handle exceptions specifically**
   - Catch specific exception types
   - Log security-relevant exceptions

5. **Keep dependencies updated**
   - Run `pip-audit` regularly
   - Update vulnerable packages promptly

6. **Encrypt sensitive data**
   - Use `DataEncryptor` for sensitive project data
   - Store encryption keys securely

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do not** create a public GitHub issue
2. Email security details to: [security contact]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Security Audit

Latest security audit: `docs/reports/src_security_assessment_revised.md`

Key findings:
- Path validation implemented
- Credential management in place
- Temporary file handling secured
- Dependency vulnerabilities tracked

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Cryptography Library](https://cryptography.io/)

