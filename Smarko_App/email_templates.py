from typing import Optional


class EmailTemplate:
    @staticmethod
    def render_base(title: str, content: str, footer: str = "") -> str:
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 15px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #1a182e 0%, #252245 100%); padding: 30px; text-align: center;">
                <h2 style="color: white; margin: 0;">{title}</h2>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                {content}
            </div>
            {f'<div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666;">{footer}</div>' if footer else ''}
        </div>
        """

    @staticmethod
    def render_2fa(code: str, name: Optional[str] = None) -> str:
        greeting = f"Hello {name}" if name else "Hello"
        content = f"""
            <p>{greeting},</p>
            <p>Your authentication code:</p>
            <div style="background: white; padding: 20px; text-align: center; border: 1px solid #ddd; margin: 20px 0;">
                <code style="font-size: 24px; font-weight: bold; letter-spacing: 4px;">{code}</code>
            </div>
            <p style="color: #666; font-size: 12px;">Valid for 2 minutes. Don't share this code.</p>
        """
        footer = "© Smarko Security - All rights reserved"
        return EmailTemplate.render_base("Smarko Login", content, footer)

    @staticmethod
    def render_password_reset(reset_link: str) -> str:
        content = f"""
            <p>Hello,</p>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background: #1a182e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="color: #666; font-size: 12px;">This link expires in 15 minutes. If you didn't request this, ignore this email.</p>
        """
        footer = "© Smarko Security - All rights reserved"
        return EmailTemplate.render_base("Password Reset", content, footer)

    @staticmethod
    def render_consent_revoked(username: Optional[str] = None) -> str:
        greeting = f"Hi {username}" if username else "Hello"
        content = f"""
            <p>{greeting},</p>
            <p>Your consent has been successfully revoked.</p>
            <p style="color: #666; font-size: 14px;">You can re-accept our terms and policies anytime by logging into your account.</p>
        """
        footer = "© Smarko Security - All rights reserved"
        return EmailTemplate.render_base("Consent Revoked", content, footer)

    @staticmethod
    def render_account_deletion(email: str, days: int = 30) -> str:
        content = f"""
            <p>Hello {email},</p>
            <p style="color: #dc3545;"><strong>Your account deletion has been requested.</strong></p>
            <p>Your account will be permanently deleted in <strong>{days} days</strong>.</p>
            <p style="color: #666; font-size: 14px;">If you want to cancel this request, you have {days} days to do so by logging into your account.</p>
        """
        footer = "© Smarko Security - All rights reserved"
        return EmailTemplate.render_base("Account Deletion Scheduled", content, footer)
