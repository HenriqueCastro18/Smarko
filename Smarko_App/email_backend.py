import logging
from django.core.mail.backends.base import BaseEmailBackend
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

logger = logging.getLogger(__name__)


class SendgridBackend(BaseEmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        count = 0
        for message in email_messages:
            try:
                if not message.to:
                    continue

                html_content = None
                if message.alternatives:
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            html_content = content
                            break

                msg = Mail(
                    from_email=message.from_email,
                    to_emails=message.to,
                    subject=message.subject,
                    plain_text_content=message.body,
                    html_content=html_content
                )
                self.client.send(msg)
                count += 1
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                if not self.fail_silently:
                    raise

        return count
