# Security Fixes Deployment Guide - Smarko

This document explains how to deploy the critical security improvements to production.

## 🔐 1. Firestore Security Rules Deployment

### What Changed
Created `firestore.rules` with comprehensive access control:
- ✓ User data isolation (can only access own documents)
- ✓ Collection-level restrictions (whitelist approach)
- ✓ Validation of data types and formats
- ✓ Immutable audit trails (security_logs, password_reset_tokens)
- ✓ Admin-only access to admin collections

### How to Deploy

**Using Firebase CLI:**

```bash
# Install Firebase CLI (if not already installed)
npm install -g firebase-tools

# Login to Firebase
firebase login

# Set your project
firebase use smarko-production

# Deploy security rules
firebase deploy --only firestore:rules
```

**Using Google Cloud Console (alternative):**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your Smarko project
3. Navigate to Firestore Database → Rules
4. Copy contents of `firestore.rules` file
5. Click "Publish"

### Verify Deployment
```bash
firebase rules:test --project=smarko-production
```

### Security Features
| Collection | Read Access | Write Access | Delete |
|-----------|----------|----------|--------|
| perfis | User only | User only | User only |
| consent_records | User + Admin | User (create), Admin (update) | Admin only |
| account_deletion_requests | User + Admin | User (create) | Admin only |
| password_reset_tokens | Backend only | Backend only | Backend only |
| security_logs | User + Admin | Backend only | Backend only |
| brute_force_protection | Backend only | Backend only | Backend only |
| 2fa_codes | Backend only | Backend only | Backend only |

---

## 🗑️ 2. Account Deletion (LGPD/GDPR 30-day Right to be Forgotten)

### What Changed
Created `delete_expired_accounts.py` management command that:
- Deletes accounts after 30-day waiting period
- Removes all user data from Firestore
- Updates Django database status to 'completed'
- Maintains audit trail of deletion

### How to Use

**Manual Execution:**
```bash
# Show what would be deleted (dry-run)
python manage.py delete_expired_accounts --dry-run

# Perform actual deletion
python manage.py delete_expired_accounts

# Custom retention period (days)
python manage.py delete_expired_accounts --days=30
```

**Schedule as Cron Job (Linux/Mac):**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2:00 AM
0 2 * * * cd /path/to/smarko && python manage.py delete_expired_accounts

# Verify cron job
crontab -l
```

**Schedule as Windows Task (Windows):**
```powershell
# Create scheduled task (run as Administrator)
$Action = New-ScheduledTaskAction -Execute "python" -Argument "manage.py delete_expired_accounts" -WorkingDirectory "C:\path\to\smarko"
$Trigger = New-ScheduledTaskTrigger -Daily -At 02:00AM
Register-ScheduledTask -TaskName "SmarkoDeleteExpiredAccounts" -Action $Action -Trigger $Trigger -RunLevel Highest
```

**Schedule on Vercel (Recommended for Production):**

Create `.vercelignore` entry to include your management script, or use a cron service:

```bash
# Using external cron service (e.g., cron-job.org, easycron.com)
# Configure to POST to your Django endpoint:
# https://smarko.app/api/maintenance/delete-expired-accounts/

# Add this view to handle the cleanup:
# See integration example below
```

### Integration with Views (Optional API Endpoint)

```python
# In views.py
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Smarko_App.management.commands.delete_expired_accounts import Command as DeleteCommand

@csrf_exempt  # Only if using API token auth
@require_http_methods(["POST"])
def delete_expired_accounts_webhook(request):
    """Trigger account deletion via webhook (for Vercel cron)"""
    # Add authentication check here!
    auth_token = request.headers.get('X-API-Key')
    if auth_token != os.getenv('MAINTENANCE_API_KEY'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    cmd = DeleteCommand()
    cmd.handle(dry_run=False, days=30)
    return JsonResponse({'status': 'ok'})
```

---

## 📁 3. Secure Temporary File Handling

### What Changed
Created `secure_files.py` utility that:
- Creates temp files in isolated directory with 0o700 permissions
- Overwrites data before deletion (3 passes + zeros)
- Automatically cleans up files after use
- Prevents unauthorized access to sensitive PDFs/HTML

### How to Use in Your Code

**Before (Unsafe):**
```python
import tempfile
import os

def generate_pdf(user_data):
    # ❌ Created in /tmp accessible to all users
    fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    
    # Write PDF...
    pdf_bytes = generate_pdf_content(user_data)
    with open(temp_path, 'wb') as f:
        f.write(pdf_bytes)
    
    # File exists in insecure location
    return temp_path
```

**After (Secure):**
```python
from Smarko_App.secure_files import SecureTemporaryFile

def generate_pdf(user_data):
    # ✓ Creates in secure directory, auto-cleaned
    with SecureTemporaryFile.temporary_file(suffix='.pdf') as temp_path:
        pdf_bytes = generate_pdf_content(user_data)
        with open(temp_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Process file (serve to user, send email, etc.)
        return serve_pdf(temp_path)
    # Auto-deleted securely when exiting context
```

**Cleanup Old Files (Run Periodically):**
```bash
# Manual cleanup of files older than 24 hours
python manage.py cleanup_temp_files --hours=24

# Run as daily cron job
0 3 * * * cd /path/to/smarko && python manage.py cleanup_temp_files
```

---

## 🔄 4. Deploy Checklist

- [ ] **Firestore Rules**
  - [ ] Test in `firestore.rules` file locally
  - [ ] Deploy via Firebase CLI: `firebase deploy --only firestore:rules`
  - [ ] Verify no errors in Firebase Console

- [ ] **Account Deletion Job**
  - [ ] Test with `--dry-run`: `python manage.py delete_expired_accounts --dry-run`
  - [ ] Schedule cron job (hourly or daily)
  - [ ] Monitor logs for errors: `tail -f logs/django.log`
  - [ ] Verify Django database is updated after deletion

- [ ] **Temporary File Cleanup**
  - [ ] Update views to use `SecureTemporaryFile.temporary_file()`
  - [ ] Test that files are actually deleted after use
  - [ ] Schedule cleanup job: `python manage.py cleanup_temp_files --hours=24`

- [ ] **Documentation**
  - [ ] Update runbook with new maintenance procedures
  - [ ] Document API keys for webhook authentication
  - [ ] Add monitoring/alerting for failed deletions

---

## 📊 Monitoring & Logging

### Monitor Account Deletions
```bash
# Check deletion logs
grep "Account deletion" logs/django.log

# Count pending deletions
python manage.py shell
>>> from Smarko_App.models import AccountDeletionRequest
>>> AccountDeletionRequest.objects.filter(status='pending').count()
```

### Monitor Temporary Files
```bash
# Check secure temp directory
ls -la /tmp/smarko_secure/

# Monitor cleanup
tail -f logs/django.log | grep "Cleaned up"
```

### Firestore Access Logs
```bash
# View Firestore audit logs in Google Cloud Console
# Cloud Logging → Logs Explorer
# Filter: resource.type="firestore_database" AND severity="ERROR"
```

---

## 🚨 Troubleshooting

### "Firebase não configurado" Error
**Problem**: `delete_expired_accounts` command fails because Firebase is not initialized
**Solution**: Ensure all `FIREBASE_*` environment variables are set in `.env`

### "Permission denied" on Temp Files
**Problem**: Temp files not being deleted on Windows
**Solution**: Ensure no other process holds file handle (check antivirus, editor)

### Firestore Rules Rejected
**Problem**: New rules syntax error
**Solution**: Validate rules with Firebase emulator:
```bash
firebase emulators:start --only firestore
firebase rules:test --project=smarko-production
```

---

## 📅 Maintenance Schedule

Recommended schedule:

| Task | Frequency | Command |
|------|-----------|---------|
| Delete expired accounts | Daily @ 2 AM | `python manage.py delete_expired_accounts` |
| Clean old temp files | Daily @ 3 AM | `python manage.py cleanup_temp_files --hours=24` |
| Verify Firestore rules | Weekly | Manual review in Firebase Console |
| Backup Firestore | Daily | `gcloud firestore export gs://smarko-backups/` |

---

## 📝 Compliance Notes

These implementations support:
- ✓ **LGPD Article 17**: Right to be forgotten (30-day deletion)
- ✓ **GDPR Article 17**: Right to erasure
- ✓ **LGPD Article 26**: Reasonable security measures
- ✓ **GDPR Article 32**: Encryption and data protection

---

**Last Updated**: 2026-05-25  
**Status**: Ready for Production Deployment
