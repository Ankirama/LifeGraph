"""
MFA (Multi-Factor Authentication) utilities and views for LifeGraph.

Implements TOTP-based two-factor authentication using django-otp.
"""

import base64
import io
from typing import Optional

import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


class IsMFAVerified(BasePermission):
    """
    Permission class that checks if user has verified MFA when required.

    If MFA_REQUIRED is True in settings and user has MFA enabled,
    the session must have mfa_verified=True.

    If MFA is not required or user doesn't have MFA enabled, permission is granted.
    """

    message = "MFA verification required. Please verify your MFA token."

    def has_permission(self, request, view):
        # Must be authenticated first
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if MFA is required globally
        mfa_required = getattr(settings, "MFA_REQUIRED", False)
        if not mfa_required:
            return True

        # Check if user has MFA enabled
        device = get_user_totp_device(request.user, confirmed=True)
        if not device:
            # User doesn't have MFA set up - depending on policy, you might
            # want to block access or allow (we allow but frontend should prompt setup)
            return True

        # User has MFA - check if session is verified
        return request.session.get("mfa_verified", False)


class IsAuthenticatedWithMFA(BasePermission):
    """
    Combined permission: IsAuthenticated + IsMFAVerified.

    Use this as a drop-in replacement for IsAuthenticated when MFA enforcement is needed.
    """

    def has_permission(self, request, view):
        return (
            IsAuthenticated().has_permission(request, view)
            and IsMFAVerified().has_permission(request, view)
        )


class MFAStatusSerializer(serializers.Serializer):
    """Serializer for MFA status response."""

    mfa_enabled = serializers.BooleanField()
    has_totp_device = serializers.BooleanField()
    mfa_required = serializers.BooleanField()
    mfa_verified = serializers.BooleanField()


class MFASetupSerializer(serializers.Serializer):
    """Serializer for MFA setup response."""

    secret = serializers.CharField()
    qr_code = serializers.CharField(help_text="Base64 encoded QR code image")
    otpauth_url = serializers.CharField()


class MFAVerifySerializer(serializers.Serializer):
    """Serializer for verifying MFA token."""

    token = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="6-digit TOTP token from authenticator app",
    )

    def validate_token(self, value):
        """Validate token is numeric."""
        if not value.isdigit():
            raise serializers.ValidationError("Token must contain only digits.")
        return value


class MFADisableSerializer(serializers.Serializer):
    """Serializer for disabling MFA."""

    token = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="6-digit TOTP token to confirm MFA disable",
    )
    password = serializers.CharField(
        write_only=True,
        help_text="Current password for confirmation",
    )


def get_user_totp_device(user, confirmed: Optional[bool] = None) -> Optional[TOTPDevice]:
    """
    Get the user's TOTP device.

    Args:
        user: The user to get the device for
        confirmed: If True, only return confirmed devices.
                   If False, only return unconfirmed devices.
                   If None, return any device.
    """
    devices = TOTPDevice.objects.filter(user=user)
    if confirmed is not None:
        devices = devices.filter(confirmed=confirmed)
    return devices.first()


def generate_totp_qr_code(device: TOTPDevice) -> str:
    """
    Generate a QR code for the TOTP device.

    Returns base64 encoded PNG image.
    """
    # Get the otpauth URL
    otpauth_url = device.config_url

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(otpauth_url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


class MFAStatusView(APIView):
    """
    Get MFA status for the current user.

    GET /api/v1/auth/mfa/status/

    Returns:
        - mfa_enabled: Whether user has MFA set up and confirmed
        - has_totp_device: Same as mfa_enabled (for compatibility)
        - mfa_required: Whether MFA is required by the system
        - mfa_verified: Whether current session is MFA verified
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        device = get_user_totp_device(request.user, confirmed=True)
        mfa_required = getattr(settings, "MFA_REQUIRED", False)
        mfa_verified = request.session.get("mfa_verified", False)

        return Response({
            "mfa_enabled": device is not None,
            "has_totp_device": device is not None,
            "mfa_required": mfa_required,
            "mfa_verified": mfa_verified,
        })


class MFASetupView(APIView):
    """
    Initialize MFA setup for the current user.

    POST /api/v1/auth/mfa/setup/

    Returns a QR code and secret for the authenticator app.
    The setup must be confirmed by verifying a token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check if user already has a confirmed device
        confirmed_device = get_user_totp_device(user, confirmed=True)
        if confirmed_device:
            return Response(
                {"detail": "MFA is already enabled. Disable it first to reconfigure."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete any unconfirmed devices
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()

        # Create new unconfirmed device
        device = TOTPDevice.objects.create(
            user=user,
            name=f"TOTP Device for {user.email}",
            confirmed=False,
        )

        # Generate QR code
        qr_code = generate_totp_qr_code(device)

        return Response({
            "secret": base64.b32encode(device.bin_key).decode(),
            "qr_code": qr_code,
            "otpauth_url": device.config_url,
        })


class MFAConfirmView(APIView):
    """
    Confirm MFA setup by verifying a token.

    POST /api/v1/auth/mfa/confirm/

    This confirms the unconfirmed TOTP device created during setup.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user = request.user

        # Get unconfirmed device
        device = get_user_totp_device(user, confirmed=False)
        if not device:
            return Response(
                {"detail": "No pending MFA setup found. Start setup first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify token
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            return Response({
                "detail": "MFA has been successfully enabled.",
                "mfa_enabled": True,
            })
        else:
            return Response(
                {"detail": "Invalid token. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MFAVerifyView(APIView):
    """
    Verify MFA token during login.

    POST /api/v1/auth/mfa/verify/

    Called after successful password authentication to complete
    the two-factor authentication process.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user = request.user

        # Get confirmed device
        device = get_user_totp_device(user, confirmed=True)
        if not device:
            return Response(
                {"detail": "MFA is not enabled for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify token
        if device.verify_token(token):
            # Mark session as MFA verified
            request.session["mfa_verified"] = True
            request.session.save()
            return Response({
                "detail": "MFA verification successful.",
                "mfa_verified": True,
            })
        else:
            return Response(
                {"detail": "Invalid token. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MFADisableView(APIView):
    """
    Disable MFA for the current user.

    POST /api/v1/auth/mfa/disable/

    Requires current password and valid TOTP token for security.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFADisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]
        user = request.user

        # Verify password
        if not user.check_password(password):
            return Response(
                {"detail": "Invalid password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get confirmed device
        device = get_user_totp_device(user, confirmed=True)
        if not device:
            return Response(
                {"detail": "MFA is not enabled for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify token
        if not device.verify_token(token):
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete all TOTP devices for user
        TOTPDevice.objects.filter(user=user).delete()

        # Clear MFA verification from session
        if "mfa_verified" in request.session:
            del request.session["mfa_verified"]
            request.session.save()

        return Response({
            "detail": "MFA has been disabled.",
            "mfa_enabled": False,
        })
