from django.core.mail import send_mail
from .models import User
from django.conf import settings
from celery import shared_task

@shared_task
def send_admin_lockout_email(user_id, lockout_minutes, ip, agent):
    user = User.objects.get(uuid=user_id)
    subject = "⚠️ Admin Account Locked Due to Failed Login Attempts"

    message = f"""
Hello {user.get_full_name() or user.email},

Your admin account has been temporarily locked due to multiple failed login attempts.

Lockout duration: {lockout_minutes} minutes


IP address and device details have been logged.
IP Address: {ip}
Device: {agent}

If this was not you, please contact support immediately.
— Uptorps Security Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@shared_task
def send_verify_email(user_id, verify_url):
    user = User.objects.get(uuid=user_id)
    email_subject= "Verify Your Email Address"

    email_message= f"""
    Hello {user.get_full_name() or user.email},

    Welcome to Uptorps! 👋
    We’re excited to have you on board.

    To complete your registration and activate your account, please verify your email address by clicking the link below:

    {verify_url}

    If you didn’t create an account with Uptorps, you can safely ignore this email.

    Thanks for joining us,
    — Uptorps Security Team
"""
    send_mail(
            subject= email_subject,
            message=email_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

@shared_task
def send_password_reset_email(user_id, reset_url, duration):
    user= User.objects.get(uuid= user_id)
    email_subject= "Password Reset Request"

    email_message= f"""
    Hello {user.get_full_name() or user.email},

    We received a request to reset the password for your account.

    To reset your password, please click the link below:
    {reset_url}

    If you did not request a password reset, you can safely ignore this email. Your password will not be changed.

    This link will expire in {duration / 60} minutes for security reasons.

    If you need help, please contact our support team.

    Best regards,
    — Uptorps Security Team
"""
    send_mail(
            subject= email_subject,
            message=email_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )  


