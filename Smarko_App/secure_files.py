import os
import tempfile
import logging
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SecureTemporaryFile:
    """Manage temporary files with secure cleanup and permissions."""

    # Create a secure temp directory with restricted permissions (700)
    SECURE_TEMP_DIR = Path(tempfile.gettempdir()) / 'smarko_secure'

    @classmethod
    def initialize(cls):
        """Create secure temp directory with restricted permissions (mode 0o700)."""
        try:
            cls.SECURE_TEMP_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
            # Ensure permissions are set correctly (in case directory already existed)
            os.chmod(cls.SECURE_TEMP_DIR, 0o700)
            logger.info(f'Secure temp directory initialized: {cls.SECURE_TEMP_DIR}')
        except OSError as e:
            logger.error(f'Failed to create secure temp directory: {e}')
            raise

    @staticmethod
    @contextmanager
    def temporary_file(suffix='', prefix='smarko_', mode='w+b'):
        """
        Context manager for secure temporary file handling.
        Automatically cleans up file after use.

        Usage:
            with SecureTemporaryFile.temporary_file(suffix='.pdf') as temp_path:
                # Write data to temp_path
                with open(temp_path, 'wb') as f:
                    f.write(pdf_data)
                # File exists while in context
            # File is automatically deleted after context exits
        """
        SecureTemporaryFile.initialize()

        temp_file = None
        try:
            # Create temp file in secure directory with restricted permissions
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix,
                prefix=prefix,
                dir=str(SecureTemporaryFile.SECURE_TEMP_DIR),
                text=('b' not in mode)
            )

            # Ensure file permissions are restrictive (0o600 = rw-------)
            os.chmod(temp_path, 0o600)

            # Close the file descriptor
            os.close(fd)

            temp_file = temp_path
            logger.debug(f'Created secure temp file: {temp_path}')

            yield temp_file

        except OSError as e:
            logger.error(f'Error creating temporary file: {e}')
            raise

        finally:
            # Secure cleanup: overwrite with random data before deletion
            if temp_file and os.path.exists(temp_file):
                try:
                    file_size = os.path.getsize(temp_file)

                    # Overwrite with random data (3 passes: random, 0x00, 0xFF)
                    with open(temp_file, 'wb') as f:
                        for _ in range(3):
                            f.write(os.urandom(file_size))

                    # Final pass: zeros
                    with open(temp_file, 'wb') as f:
                        f.write(b'\x00' * file_size)

                    os.remove(temp_file)
                    logger.debug(f'Securely deleted temp file: {temp_file}')

                except OSError as e:
                    logger.error(f'Error deleting temporary file {temp_file}: {e}')

    @staticmethod
    def cleanup_old_files(hours=24):
        """
        Clean up old temporary files (useful as periodic maintenance task).
        Deletes files older than specified hours.
        """
        import time

        SecureTemporaryFile.initialize()

        cutoff_time = time.time() - (hours * 3600)
        deleted_count = 0

        try:
            for file_path in SecureTemporaryFile.SECURE_TEMP_DIR.glob('smarko_*'):
                if file_path.is_file():
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            logger.debug(f'Cleaned up old temp file: {file_path}')
                        except OSError as e:
                            logger.warning(f'Failed to clean up {file_path}: {e}')

            logger.info(f'Cleaned up {deleted_count} old temporary files')
            return deleted_count

        except OSError as e:
            logger.error(f'Error during cleanup: {e}')
            return 0
