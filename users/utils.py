import qrcode
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random

import os
from datetime import datetime
from .models import Subscription




def generate_user_qr(user):
    # البحث عن اشتراك فعّال
    now = timezone.now()
    active_sub = Subscription.objects.filter(
        user=user, is_active=True, end_date__gte=now
    ).first()

    # تكوين النص داخل QR
    data = f"User ID: {user.id}, Name: {user.name}, Phone: {user.phone}"

    if active_sub:
        data += f", Plan: {active_sub.plan.name}, Start: {active_sub.start_date.strftime('%Y-%m-%d')}, End: {active_sub.end_date.strftime('%Y-%m-%d')}"

    # إنشاء QR
    qr = qrcode.make(data)

    # مسار الحفظ
    qr_dir = os.path.join(settings.MEDIA_ROOT, "qr_codes")
    os.makedirs(qr_dir, exist_ok=True)

    filename = f"user_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    file_path = os.path.join(qr_dir, filename)

    qr.save(file_path)

    return f"/media/qr_codes/{filename}"





def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, code):
    subject = "رمز التحقق الخاص بك"
    message = f"رمز التحقق هو: {code}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
