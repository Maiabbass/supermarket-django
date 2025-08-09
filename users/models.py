from django.db import models
from django.utils import timezone
import os
from django.conf import settings

def user_qr_path(instance, filename):
    return os.path.join('qrcodes', f"user_{instance.id}.png")

class User(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)
    password_hash = models.CharField(max_length=255)
    is_subscriber = models.BooleanField(default=False)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    qr_code = models.ImageField(upload_to=user_qr_path, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    loyalty_points = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)




# ✅ موديلات الاشتراك المدمجة من subscriptions/models.py
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    duration_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.plan.name}"