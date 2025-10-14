# PKCE Security Integration Test

This document describes the comprehensive security test suite for the OAuth PKCE flow vulnerability fix.

## Overview

The `security-test.html` file is a comprehensive integration test that validates:

1. ✅ **PKCE Login Flow** - Complete authentication with token storage
2. ✅ **Logout Functionality** - Proper cleanup of authentication state
3. 🛡️ **Security Protection** - Prevention of token leakage to malicious domains
4. 🔄 **UI State Management** - Correct UI updates for all authentication states
5. 🚫 **Public Deployment Exclusion** - Test file not accessible on public domain

## Running the Test

### Local Development

Run the security test locally using the Makefile:

```bash
# For WASM/preview environment (port 8088)
make security-test

# For Python development environment (port 2718)
make security-test-dev
```

**Port 8088 (Preview Mode):**
- Compatible with `make preview` OAuth redirects
- Tests WASM build security fixes
- URL: `http://localhost:8088/security-test.html`

**Port 2718 (Development Mode):**
- Compatible with `make edit` OAuth redirects
- Tests with live Python notebooks
- URL: `http://localhost:2718/security-test.html`

⚠️ **Important:** OAuth login will only work on ports 2718 or 8088 due to redirect URI configuration.

### Manual Testing

You can also serve the files manually:

```bash
npx wrangler pages dev --port 8088 --local
```

Then navigate to `http://localhost:8088/security-test.html`

## Test Scenarios

### 1. Authentication Flow Tests

- **Login**: Tests simulated PKCE authentication flow
- **Token Storage**: Verifies tokens are stored in localStorage
- **UI Updates**: Confirms authentication state changes UI properly
- **Logout**: Tests complete cleanup of authentication data

### 2. Security Protection Tests

- **Malicious Redirects**: Tests redirects to untrusted domains (e.g., `evil-attacker.com`)
  - ✅ Should clear tokens before redirect
  - 🛡️ Prevents token theft
  
- **Safe Redirects**: Tests redirects to trusted domains (e.g., `notebooks.cloudflare.com`)
  - ✅ Should preserve tokens
  - 🔄 Maintains authentication state

### 3. Integration Tests

The "Run Complete Integration Test" button executes a full end-to-end test:

1. Logout (clean state)
2. PKCE Login (authenticate)
3. Safe redirect (preserve tokens)
4. Malicious redirect test (clear tokens)
5. Logout (cleanup)
6. Verify no tokens remain

## Security Fix Validation

The test validates the security fix addresses the HackerOne vulnerability:

### ❌ **Before Fix** (Vulnerable)
```javascript
// Vulnerable code - direct redirect without protection
window.location.href = redirectUrl.toString();
```

### ✅ **After Fix** (Protected)
```javascript
// Protected code - clears tokens before external redirects
function safeRedirect(url) {
    if (isExternalDomain(url)) {
        // Clear sensitive tokens before redirecting to external domains
        clearAuthTokens();
    }
    window.location.href = url;
}
```

## Test File Exclusion

The `security-test.html` file is excluded from public deployment via:

1. **_routes.json**: Excludes `/security-test.html` from public routes
2. **Local Only**: File only accessible during local development
3. **Build Process**: Not copied to production export directory

## Expected Results

When running the test suite, you should see:

- 🟢 **All authentication tests pass**
- 🟢 **All security protection tests pass** 
- 🟢 **All integration tests pass**
- 🛡️ **Token leakage prevented** for malicious domains
- 🔄 **PKCE flow preserved** for legitimate domains
- 🚫 **Test file inaccessible** on public domain

## Files Modified

The security fix was implemented in:

- `notebooks/public/login.html` - Main OAuth callback handler
- `moutils/demos/cloudflare/public/login.html` - Moutils OAuth callback handler

Both files now include:
- `isExternalDomain()` - Identifies untrusted domains
- `safeRedirect()` - Clears tokens before external redirects
- Preserves PKCE functionality for legitimate OAuth flows

## Threat Model

This fix addresses the specific vulnerability where:

1. **Attack Vector**: Malicious redirect URL in base64-encoded OAuth `state` parameter
2. **Exploitation**: Victim redirected to attacker-controlled domain with tokens still in localStorage
3. **Impact**: Complete Cloudflare account takeover via stolen access tokens
4. **Mitigation**: Clear sensitive tokens before redirecting to untrusted domains

The fix maintains the legitimate PKCE OAuth flow while preventing token theft.
