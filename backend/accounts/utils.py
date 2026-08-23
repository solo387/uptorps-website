from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings

token_duration_timer = settings.TOKEN_VERIFICATION_DURATION
signer = TimestampSigner()

def generate_email_verification_token(user):
    return signer.sign(user.email)

def verify_email_token(token, max_age=token_duration_timer):  # 30 mins
    try:
        email = signer.unsign(token, max_age=max_age)
        return email
    except (BadSignature, SignatureExpired):
        return None

def generate_password_reset_token(user):
    return signer.sign(user.email)

def verify_password_reset_token(token, max_age=token_duration_timer):  # 30 mins
    try:
        email = signer.unsign(token, max_age=max_age)
        return email
    except (BadSignature, SignatureExpired):
        return None