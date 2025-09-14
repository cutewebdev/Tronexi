import pyotp
import qrcode
import io
import base64
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

User = get_user_model()


# ✅ Generate QR Code for Google Authenticator
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_qr(request):
    user = request.user

    # Check if user already has a TOTP device
    existing_device = TOTPDevice.objects.filter(user=user, name="default").first()
    if existing_device:
        return Response({"message": "OTP already set up"}, status=400)

    # Create a new TOTP device
    device = TOTPDevice.objects.create(user=user, name="default")

    # Generate Base32 key for pyotp
    secret_key = base64.b32encode(device.bin_key).decode()

    # Create TOTP URI for Google Authenticator
    otp_uri = pyotp.TOTP(secret_key).provisioning_uri(
        name=user.username,
        issuer_name="MyBrokerageApp"
    )

    # Generate QR code as base64 image
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(otp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return Response({
        "message": "QR Code generated successfully",
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "otp_uri": otp_uri
    }, status=200)


# ✅ Verify OTP Code
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_otp(request):
    user = request.user
    otp_code = request.data.get("otp")

    if not otp_code:
        return Response({"error": "OTP code is required"}, status=400)

    # Get the user's TOTP device
    device = TOTPDevice.objects.filter(user=user, name="default").first()
    if not device:
        return Response({"error": "No OTP device found"}, status=404)

    # Convert binary key to Base32 for pyotp
    secret_key = base64.b32encode(device.bin_key).decode()
    totp = pyotp.TOTP(secret_key)

    if totp.verify(otp_code, valid_window=1):  # allow slight time drift
        return Response({"message": "OTP verified successfully"}, status=200)
    else:
        return Response({"error": "Invalid OTP"}, status=400)


# ✅ Send Backup Email OTP
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_backup_email(request):
    user = request.user
    email = user.email

    # Generate random 6-digit OTP
    email_otp = str(random.randint(100000, 999999))

    # Store OTP in session for now (You can use Redis or DB for production)
    request.session['email_otp'] = email_otp

    # Send email
    send_mail(
        subject="Your Backup OTP Code",
        message=f"Your OTP code is: {email_otp}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response({"message": "Backup OTP sent to your email"}, status=200)


# ✅ Verify Backup Email OTP
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email_otp(request):
    user_otp = request.data.get("otp")
    session_otp = request.session.get('email_otp')

    if not user_otp:
        return Response({"error": "OTP is required"}, status=400)

    if not session_otp:
        return Response({"error": "No OTP found. Request a new one."}, status=400)

    if user_otp == session_otp:
        # Clear OTP after success
        del request.session['email_otp']
        return Response({"message": "Email OTP verified successfully"}, status=200)
    else:
        return Response({"error": "Invalid OTP"}, status=400)