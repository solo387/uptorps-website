from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from audits.signals import failed_admin_login, success_admin_login
from .emails import send_admin_lockout_email, send_verify_email
from rest_framework.exceptions import AuthenticationFailed
from .utils import generate_email_verification_token
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from accounts.models import User
from datetime import timedelta
from math import ceil
from referral.models import PendingReferral, ReferralNode
from referral.utils import validate_referral_code


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    referral_code = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "referral_code",
        )

    def create(self, validated_data):
        referral_code = validated_data.pop("referral_code", None)
        user = User.objects.create_user(
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            username=validated_data.get("username", None),
            email=validated_data.get("email"),
            password=validated_data["password"],
            is_active=False,
            email_verified=False,
        )

        # handle referral code if provided
        if referral_code:
            node = validate_referral_code(referral_code)

            if node:
                # store permanently on the user record
                user.referral_code_used = referral_code
                user.save(update_fields=["referral_code_used"])

                # create the pending referral record
                PendingReferral.objects.create(
                    referred_user=user, referrer=node.user, referral_code=referral_code
                )
            # node = ReferralNode.objects.create(
            # user          = user,
            # parent_node   = parent_node,
            # depth         = parent_node.depth + 1,
            # referral_code = generate_referral_code(user),
            # status        = ReferralNode.Status.ACTIVE,
            # root_node     = parent_node.root_node   # inherit from parent
            #     )
        # else:
        #     # step 1 — create the node without root_node
        #     node = ReferralNode.objects.create(
        #         user=user,
        #         parent_node=None,
        #         depth=1,
        #         referral_code=generate_referral_code(user),
        #         status=ReferralNode.Status.ACTIVE,
        #         root_node=None,  # temporarily null
        #     )

        #     # step 2 — now the node has an ID, point it to itself
        #     node.root_node = node
        #     node.save(update_fields=["root_node"])
        token = generate_email_verification_token(user)
        verify_url = f"{settings.HOST_DOMAIN_URL}/verify-email?token={token}"
        send_verify_email.delay(f'{user.uuid}', verify_url)
        return user


# class AdminCreateSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)

#     class Meta:
#         model = User
#         fields = ("username", "email", "password")

#     def create(self, validated_data):
#         user = User.objects.create_user(
#             username=validated_data["username"],
#             email=validated_data.get("email"),
#             password=validated_data["password"],
#         )
#         user.role = User.Roles.ADMIN
#         user.is_staff = True
#         user.email_verified = True
#         user.is_active = True
#         user.save()
#         return user


class AdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "password",
            "role",
            "admin_type",
            "dev_specialization",
        )

    def validate(self, attrs):
        request = self.context["request"]
        actor = request.user

        # 🔒 Only managers can create admins
        # if not actor.is_backend_dev:
        #     raise serializers.ValidationError(
        #         "Only backend developers can create admin accounts."
        #     )

        # 🔒 Role must be admin
        if attrs.get("role") != User.Roles.ADMIN:
            raise serializers.ValidationError(
                "Only admin accounts can be created via this endpoint."
            )

        admin_type = attrs.get("admin_type")
        dev_spec = attrs.get("dev_specialization")

        # 🔒 Admin type required
        if not admin_type:
            raise serializers.ValidationError("admin_type is required.")

        # 🔒 Developer must have specialization
        if admin_type == User.AdminType.DEVELOPER and not dev_spec:
            raise serializers.ValidationError(
                "Developer admins must have a specialization."
            )

        # 🔒 Manager must not have specialization
        if admin_type == User.AdminType.MANAGER and dev_spec:
            raise serializers.ValidationError(
                "Managers cannot have a dev specialization."
            )

        return attrs

    def create(self, validated_data):
        firstname = validated_data.get("first_name", None)
        lastname = validated_data.get("last_name", None)
        username = validated_data["username"]
        password = validated_data.pop("password")
        email = validated_data["email"]
        # user = User.objects.create(
        #     username= username,
        #     email=email,
        #     first_name= firstname,
        #     last_name= lastname
        #     )
        user = User(**validated_data)
        user.role = User.Roles.ADMIN
        user.admin_type = validated_data.get("admin_type", None)
        user.dev_specialization = validated_data.get("dev_specialization", None)
        user.set_password(password)
        user.is_staff = True
        user.is_active = True
        user.email_verified = True
        user.save()
        return user
        # return

    # JWT login serializer custom


MAX_FAILED_ATTEMPTS = 5  # This is to help keep track of attempts before locking account
LOCKOUT_MINUTES = 15  # This is the minutes user of the account will have to wait


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        request = self.context.get("request")

        # Try to fetch user FIRST (for lockout check)
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            user_obj = None

        # LOCKOUT CHECK (admins only)
        if user_obj and user_obj.is_staff:
            now = timezone.now()

            # Lockout is still active
            if user_obj.locked_until and user_obj.locked_until > now:
                remaining_minutes = ceil(
                    (user_obj.locked_until - now).total_seconds() / 60
                )
                raise AuthenticationFailed(
                    f"Admin account locked. Try again later in {remaining_minutes} minutes."
                )

            # Lockout period has expired - reset counters
            if user_obj.locked_until and user_obj.locked_until <= now:
                user_obj.failed_login_attempts = 0
                user_obj.locked_until = None
                user_obj.save(
                    update_fields=[
                        "failed_login_attempts",
                        "locked_until",
                    ]
                )


        user = authenticate(
            request=request,
            email=email,
            password=password,
        )

        if not user:
            # FAILED LOGIN
            # Admin account lock down implementation
            if user_obj and user_obj.is_staff:
                user_obj.failed_login_attempts += 1

                if user_obj.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user_obj.locked_until = timezone.now() + timedelta(
                        minutes=LOCKOUT_MINUTES
                    )
                    request = self.context["request"]

                    ip = request.META.get("REMOTE_ADDR", "Unknown")
                    agent = request.META.get("HTTP_USER_AGENT", "Unknown")
                    send_admin_lockout_email.delay(
                        str(user_obj.uuid),
                        LOCKOUT_MINUTES,
                        ip,
                        agent,
                    )
                user_obj.save(update_fields=["failed_login_attempts", "locked_until"])

            # Emit signal ONLY on failure
            failed_admin_login.send(
                sender=self.__class__,
                email=email,
                request=request,
            )
            raise AuthenticationFailed(
                detail="No active account found with the given credentials",
                code="no_active_account",
            )
        else:
            # ✅ SUCCESSFUL LOGIN
            if user.is_staff:
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save(update_fields=["failed_login_attempts", "locked_until"])

                success_admin_login.send(
                    sender=self.__class__,
                    email=email,
                    request=request,
                )

        if not user.email_verified:
            raise AuthenticationFailed("Email not verified")

        if not user.is_active:
            raise AuthenticationFailed("Account inactive")

        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "uuid": str(user.uuid),
            "email": user.email,
            # "role": user.role
        }
        return data


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "uuid",
            "email",
            "role",
            "admin_type",
            "dev_specialization",
            "is_active",
            "date_joined",
        ]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "admin_type",
            "dev_specialization",
            # "is_active",
        ]

    def update(self, instance, validated_data):
        if self.context["request"].method == "PUT":
            required_fields = {"email"}
            missing = required_fields - validated_data.keys()
            if missing:
                raise serializers.ValidationError(f"Missing required fields: {missing}")
        return super().update(instance, validated_data)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        # Non-admins cannot modify restricted fields
        restricted_fields = {"role", "admin_type", "dev_specialization", "is_active"}

        if not user.is_admin and not user.is_backend_dev:
            for field in restricted_fields:
                if field in attrs:
                    raise serializers.ValidationError(
                        {field: "You are not allowed to modify this field."}
                    )

        return attrs
