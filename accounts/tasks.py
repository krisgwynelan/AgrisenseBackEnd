from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from datetime import datetime, time
from accounts.models import SensorReading
from django.db.models import Avg
from django.utils import timezone

User = get_user_model()

@shared_task
def send_daily_summary():
    """
    Send a minimal WebSocket notification to all users using the daily average of soil sensor data.
    """
    print("📤 Celery task running... Calculating daily soil summary")

    # ✅ Always use timezone-aware datetime
    now = timezone.now()

    # 🟢 Get start & end of the current day (timezone correct)
    local_today = timezone.localdate()
    start_of_day = timezone.make_aware(datetime.combine(local_today, time.min))
    end_of_day = timezone.make_aware(datetime.combine(local_today, time.max))

    channel_layer = get_channel_layer()

    # ✅ Calculate daily averages safely
    daily_avg = SensorReading.objects.filter(
        timestamp__range=(start_of_day, end_of_day)
    ).aggregate(
        temperature_avg=Avg("temperature"),
        ph_avg=Avg("ph"),
        nitrogen_avg=Avg("nitrogen"),
        phosphorus_avg=Avg("phosphorus"),
        potassium_avg=Avg("potassium"),
    )

    # If there's no temperature data → nothing for today
    if not daily_avg["temperature_avg"]:
        print("⚠️ No sensor data found for today.")
        return

    # Prepare data payload (safe rounding)
    data_payload = {
        "temperature": round(daily_avg["temperature_avg"], 1),
        "ph": round(daily_avg["ph_avg"], 2),
        "nitrogen": round(daily_avg["nitrogen_avg"], 1),
        "phosphorus": round(daily_avg["phosphorus_avg"], 1),
        "potassium": round(daily_avg["potassium_avg"], 1),
    }

    print(f"🌱 Daily average reading: {data_payload}")

    # Broadcast to all users
    for user in User.objects.all():
        group_name = f"user_{user.id}"

        message = {
            "title": "🌿 Daily Soil Summary",
            "message": (
                f"🌡 {data_payload['temperature']}°C | 💧 pH: {data_payload['ph']} | "
                f"🌿 N:{data_payload['nitrogen']} P:{data_payload['phosphorus']} K:{data_payload['potassium']}"
            ),
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": data_payload,
        }

        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",
                    "message": message,
                    "timestamp": now.isoformat(),
                },
            )
            print(f"📩 Sent to {user.username}: {data_payload}")

        except Exception as e:
            print(f"⚠️ Failed to send to {user.username}: {e}")

    print("✅ Celery broadcast complete.")
