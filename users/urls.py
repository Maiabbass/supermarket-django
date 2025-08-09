from django.urls import path

from users import views
from .views import (
    RegisterView, ResendOTPView, VerifyOTPView,
    LoginView, ResetPasswordView, ChangePasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('resend-otp/', ResendOTPView.as_view()),
    path('verify-otp/', VerifyOTPView.as_view()),
    path('login/', LoginView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('check/<int:user_id>/', views.check_user_subscription),
    path('plans/', views.get_subscription_plans),
    path('request/', views.request_subscription),
    path('activate/', views.activate_user_subscription),
    path('all-users/', views.list_all_users_with_subscription_status),
    path('create-plan/', views.create_subscription_plan),
]

