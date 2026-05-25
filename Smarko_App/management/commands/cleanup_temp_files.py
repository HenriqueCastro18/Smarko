from django.core.management.base import BaseCommand
from Smarko_App.secure_files import SecureTemporaryFile


class Command(BaseCommand):
    help = 'Clean up old temporary files (security: prevents sensitive data exposure)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Delete files older than N hours (default: 24)',
        )

    def handle(self, *args, **options):
        hours = options['hours']

        deleted_count = SecureTemporaryFile.cleanup_old_files(hours=hours)

        self.stdout.write(
            self.style.SUCCESS(f'✓ {deleted_count} arquivo(s) temporário(s) deletado(s)')
        )
