"""
Django management command: cleanup_expired_data

Implements LGPD data retention policy:
- Remove security logs older than 90 days
- Remove rate limit buckets older than 24 hours
- Delete accounts marked for deletion (after 30-day grace period)
- Anonymize revoked consent records

Run with: python manage.py cleanup_expired_data [--dry-run]
Schedule: Via cron (daily) or Celery (periodic task)
"""

from typing import Dict, Any
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from firebase_admin import firestore

from Smarko_App.utils import get_firestore_client, log_security_event


class Command(BaseCommand):
    """Django management command for data cleanup and retention policy."""

    help = 'Cleanup expired data according to LGPD retention policy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        """Execute cleanup operations."""
        dry_run = options.get('dry_run', False)
        db = get_firestore_client()

        if not db:
            raise CommandError('Firestore not configured')

        self.stdout.write(self.style.WARNING(
            f'🧹 Starting cleanup... (dry_run={dry_run})'
        ))

        try:
            # Run cleanup operations
            results = {
                'logs_deleted': self._cleanup_old_logs(db, dry_run),
                'rate_limits_deleted': self._cleanup_rate_limits(db, dry_run),
                'blacklist_deleted': self._cleanup_session_blacklist(db, dry_run),
                'accounts_deleted': self._cleanup_scheduled_deletions(db, dry_run),
                'consents_anonymized': self._anonymize_revoked_consents(db, dry_run),
            }

            # Print summary
            self.stdout.write(self.style.SUCCESS('\n✅ Cleanup Complete:'))
            for operation, count in results.items():
                self.stdout.write(f'  {operation}: {count} items')

            if dry_run:
                self.stdout.write(self.style.WARNING(
                    '\n⚠️  DRY RUN: No data was actually deleted'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Cleanup failed: {e}'))
            raise CommandError(f'Cleanup operation failed: {e}')

    def _cleanup_old_logs(self, db, dry_run: bool) -> int:
        """Delete security logs older than 90 days."""
        cutoff_date = timezone.now() - timedelta(days=90)

        query = db.collection('logs_seguranca').where(
            'data_hora', '<', cutoff_date
        )
        docs = query.stream()

        count = 0
        for doc in docs:
            if not dry_run:
                doc.reference.delete()
            count += 1

        self.stdout.write(f'  → logs_seguranca: {count} documents (>90 days old)')
        return count

    def _cleanup_rate_limits(self, db, dry_run: bool) -> int:
        """Delete expired rate limit buckets (>24 hours old)."""
        cutoff_date = timezone.now() - timedelta(hours=24)

        query = db.collection('rate_limit_buckets').where(
            'last_refill', '<', cutoff_date
        )
        docs = query.stream()

        count = 0
        for doc in docs:
            if not dry_run:
                doc.reference.delete()
            count += 1

        self.stdout.write(f'  → rate_limit_buckets: {count} documents (>24 hours old)')
        return count

    def _cleanup_session_blacklist(self, db, dry_run: bool) -> int:
        """Delete expired session blacklist entries."""
        cutoff_date = timezone.now()

        query = db.collection('sessions_blacklist').where(
            'expires_at', '<', cutoff_date
        )
        docs = query.stream()

        count = 0
        for doc in docs:
            if not dry_run:
                doc.reference.delete()
            count += 1

        self.stdout.write(f'  → sessions_blacklist: {count} documents (expired)')
        return count

    def _cleanup_scheduled_deletions(self, db, dry_run: bool) -> int:
        """Delete accounts scheduled for deletion (after 30-day grace period)."""
        cutoff_date = timezone.now()

        query = db.collection('account_deletion_requests').where(
            'status', '==', 'pending'
        ).where(
            'deletion_scheduled_for', '<', cutoff_date
        )
        docs = list(query.stream())

        count = 0
        for doc in docs:
            data = doc.to_dict()
            uid = data.get('firebase_uid')
            email = data.get('email')

            if not dry_run:
                # Delete user profile
                try:
                    db.collection('perfis').document(uid).delete()
                    db.collection('consent_records').document(uid).delete()
                    # Mark deletion as completed
                    doc.reference.update({'status': 'completed', 'deleted_at': firestore.SERVER_TIMESTAMP})
                    # Log deletion
                    log_security_event(
                        uid, email, 'account_auto_deleted_after_grace_period',
                        'system', status='success'
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'    Error deleting {uid}: {e}'
                    ))
                    continue

            count += 1

        self.stdout.write(f'  → accounts: {count} accounts deleted (>30 days scheduled)')
        return count

    def _anonymize_revoked_consents(self, db, dry_run: bool) -> int:
        """Anonymize revoked consent records older than 30 days."""
        cutoff_date = timezone.now() - timedelta(days=30)

        query = db.collection('consent_records').where(
            'is_active', '==', False
        ).where(
            'revoked_at', '<', cutoff_date
        )
        docs = query.stream()

        count = 0
        for doc in docs:
            if not dry_run:
                # Anonymize: remove PII, keep only metadata
                doc.reference.update({
                    'firebase_uid': 'ANONYMIZED',
                    'email': 'ANONYMIZED',
                    'ip_address': 'ANONYMIZED',
                    'user_agent': 'ANONYMIZED',
                    'anonymized_at': firestore.SERVER_TIMESTAMP,
                })
            count += 1

        self.stdout.write(f'  → consents: {count} consents anonymized (>30 days revoked)')
        return count
