import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
import firebase_admin
from firebase_admin import firestore

from Smarko_App.models import AccountDeletionRequest
from Smarko import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete user accounts that have completed their 30-day deletion period (LGPD compliance)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to wait before deletion (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']

        db = settings.db
        if not db:
            self.stdout.write(self.style.ERROR('❌ Firebase não configurado'))
            return

        threshold_date = timezone.now() - timedelta(days=days)

        # Find all pending deletion requests that are overdue
        overdue_requests = AccountDeletionRequest.objects.filter(
            status='pending',
            deletion_scheduled_for__lte=threshold_date
        )

        count = overdue_requests.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ Nenhuma conta aguardando exclusão'))
            return

        self.stdout.write(
            self.style.WARNING(f'⚠️ Encontradas {count} conta(s) para deletar')
        )

        for deletion_request in overdue_requests:
            try:
                uid = deletion_request.firebase_uid
                email = deletion_request.email

                if dry_run:
                    self.stdout.write(f'  [DRY-RUN] Deletaria: {email} (UID: {uid})')
                    continue

                self._delete_user_data(db, uid, email)

                # Mark as completed in Django
                deletion_request.status = 'completed'
                deletion_request.save()

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Deletado: {email} (UID: {uid})')
                )
                logger.info(f'Account deletion completed for: {email} (UID: {uid})')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao deletar {deletion_request.email}: {str(e)}')
                )
                logger.error(f'Failed to delete account {deletion_request.email}: {str(e)}')

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Exclusão de {count} conta(s) concluída')
            )

    def _delete_user_data(self, db, uid, email):
        """Delete all user data from Firestore (LGPD right to be forgotten)"""

        collections_to_clean = [
            ('perfis', uid),
            ('consent_records', 'firebase_uid'),
            ('security_logs', 'firebase_uid'),
            ('password_reset_tokens', 'email'),
            ('account_deletion_requests', 'firebase_uid'),
        ]

        for collection_name, field_name in collections_to_clean:
            try:
                query = db.collection(collection_name)

                if collection_name == 'perfis':
                    # For perfis, use direct document access
                    doc = db.collection(collection_name).document(uid)
                    if doc.get().exists:
                        doc.delete()
                else:
                    # For other collections, query by field
                    docs = query.where(field_name, '==', uid if field_name == 'firebase_uid' else email).stream()
                    for doc in docs:
                        doc.reference.delete()

            except Exception as e:
                logger.warning(f'Failed to clean {collection_name} for {uid}: {str(e)}')
                raise

        logger.info(f'All Firestore data deleted for user: {email} (UID: {uid})')
