from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from firebase_admin import firestore
from django.db.models import Q
from Smarko_App.models import LogSeguranca

class Command(BaseCommand):
    help = 'Delete audit logs older than 6 months (LGPD compliance - Art. 15-18)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=180,
            help='Number of days to keep (default: 180 = 6 months)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_to_keep = options['days']

        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        self.stdout.write(
            self.style.WARNING(f'Cleaning logs older than {days_to_keep} days ({cutoff_date.date()})')
        )

        count_firestore = 0

        # ========== Firestore Cleanup ==========
        try:
            db = firestore.client()

            # Query logs older than cutoff date
            logs_query = db.collection('logs_seguranca').where(
                'data_hora', '<', cutoff_date
            ).stream()

            deleted_docs = []

            for log in logs_query:
                deleted_docs.append(log.id)
                if not dry_run:
                    log.reference.delete()
                count_firestore += 1

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'[DRY RUN] Would delete {count_firestore} logs from Firestore')
                )
                if deleted_docs[:5]:
                    self.stdout.write(f'  Examples: {", ".join(deleted_docs[:5])}')
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Deleted {count_firestore} logs from Firestore')
                )

        except ValueError as e:
            if 'Firebase app does not exist' in str(e):
                self.stdout.write(
                    self.style.WARNING('[INFO] Firebase not initialized (development mode) - skipping Firestore cleanup')
                )
                count_firestore = 0
            else:
                self.stdout.write(
                    self.style.ERROR(f'[ERROR] Error accessing Firestore: {str(e)}')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'[ERROR] Error accessing Firestore: {str(e)}')
            )
            return

        try:
            old_logs_django = LogSeguranca.objects.filter(
                data_hora__lt=cutoff_date
            )

            count_django = old_logs_django.count()

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'[DRY RUN] Would delete {count_django} logs from Django database')
                )
            else:
                old_logs_django.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Deleted {count_django} logs from Django database')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'[ERROR] Error deleting Django logs: {str(e)}')
            )
            return

        # ========== Summary ==========
        total_deleted = count_firestore + count_django

        self.stdout.write(
            self.style.SUCCESS(f'\n[SUCCESS] Cleanup completed!')
        )
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  - Firestore logs deleted: {count_firestore}')
        self.stdout.write(f'  - Django database logs deleted: {count_django}')
        self.stdout.write(f'  - Total deleted: {total_deleted}')
        self.stdout.write(f'  - Cutoff date: {cutoff_date.strftime("%d/%m/%Y %H:%M:%S")}')
        self.stdout.write(f'  - Retention period: {days_to_keep} days')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n[DRY RUN] No data was actually deleted. Run without --dry-run to execute.')
            )

        # ========== LGPD Compliance Note ==========
        self.stdout.write(
            self.style.WARNING(
                f'\n[LGPD] Compliance: Art. 15-18\n'
                f'   - Logs older than {days_to_keep} days are deleted\n'
                f'   - Consent Records are kept (permanent proof)\n'
                f'   - User data is accessible via /user-data/\n'
                f'   - Users can request deletion via /request-deletion/\n'
            )
        )
