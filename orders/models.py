from django.db import models
from django.utils import timezone
import os

def invoice_qr_path(instance, filename):
    return os.path.join('invoice_qr', f"invoice_{instance.id}.png")

class Invoice(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=(('pending','Pending'),('paid','Paid')))
    qr_code = models.ImageField(upload_to=invoice_qr_path, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
