from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Avg
from .models import PasswordResetOTP, SensorReading, DailySummary
from .serializers import SensorReadingSerializer, DailySummarySerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ✅ LOGIN USER
@csrf_exempt
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials"}, status=401)

    login(request, user)

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        "message": "Login successful",
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "token": access_token,
    })


# ✅ REGISTER USER
@csrf_exempt
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def register_user(request):
    data = request.data
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")

    if not username or not password:
        return Response({"error": "Username and password are required."}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists."}, status=400)

    if email and User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists."}, status=400)

    user = User.objects.create_user(
        username=username,
        email=email or "",
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    return Response({"message": "User registered successfully."}, status=201)


# ✅ SEND RESET OTP
@csrf_exempt
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def send_reset_otp(request):
    email = request.data.get("email")
    if not email:
        return Response({"message": "Email is required."}, status=400)

    try:
        user = User.objects.get(email=email)
        otp = get_random_string(length=6, allowed_chars="0123456789")

        PasswordResetOTP.objects.filter(user=user).delete()

        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            subject="AgriSense Password Reset OTP",
            message=f"Your OTP for password reset is: {otp}\n\nThis OTP will expire in 10 minutes.",
            from_email="noreply@agrisense.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "OTP sent to your email."}, status=200)

    except User.DoesNotExist:
        return Response({"message": "Email not found."}, status=404)


# ✅ VERIFY OTP
@csrf_exempt
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")
    if not email or not otp:
        return Response({"message": "Email and OTP are required."}, status=400)

    try:
        user = User.objects.get(email=email)
        record = PasswordResetOTP.objects.get(user=user)

        if timezone.now() - record.created_at > timedelta(minutes=10):
            record.delete()
            return Response({"message": "OTP expired. Please request a new one."}, status=400)

        if record.otp == otp:
            return Response({"message": "OTP verified."}, status=200)
        else:
            return Response({"message": "Invalid OTP."}, status=400)

    except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
        return Response({"message": "Invalid request."}, status=400)


# ✅ RESET PASSWORD
@csrf_exempt
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def reset_password(request):
    email = request.data.get("email")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if not email or not new_password or not confirm_password:
        return Response({"message": "All fields are required."}, status=400)

    if new_password != confirm_password:
        return Response({"message": "Passwords do not match."}, status=400)

    try:
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        PasswordResetOTP.objects.filter(user=user).delete()

        return Response({"message": "Password reset successful."}, status=200)
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=404)


# ✅ STORE SENSOR READING
@csrf_exempt
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def store_sensor_reading(request):
    serializer = SensorReadingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ STORE DAILY SUMMARY
@csrf_exempt
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def store_daily_summary(request):
    try:
        date_str = request.data.get("date")
        if not date_str:
            return Response({"error": "Date is required."}, status=400)

        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = timezone.now().date()

        if selected_date > today:
            return Response({"error": "Cannot store future dates."}, status=400)

        # Check if summary exists
        existing_summary = DailySummary.objects.filter(date=selected_date).first()

        if existing_summary:
            # Update existing summary
            serializer = DailySummarySerializer(existing_summary, data=request.data, partial=True)
        else:
            # Create new summary
            serializer = DailySummarySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            action = "updated" if existing_summary else "created"
            return Response({"message": f"Daily summary {action} successfully.", "data": serializer.data}, status=201)

        return Response(serializer.errors, status=400)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# ✅ SOIL SUMMARY (GET)
@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
def soil_summary(request):
    date_str = request.GET.get("date")
    if not date_str:
        return Response({"error": "Date required"}, status=400)

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        readings = SensorReading.objects.filter(timestamp__date=selected_date).order_by("timestamp")

        data = [
            {
                "timestamp": r.timestamp,
                "temperature": r.temperature,
                "ph": r.ph,
                "nitrogen": r.nitrogen,
                "phosphorus": r.phosphorus,
                "potassium": r.potassium,
            }
            for r in readings
        ]

        return Response({"data": data}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)