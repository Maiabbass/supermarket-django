from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, SubscriptionPlan, User, OTPCode
from .utils import generate_otp, generate_user_qr, send_otp_email
from .serializers import RegisterSerializer, LoginSerializer, ResetPasswordSerializer, ChangePasswordSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser



class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            if User.objects.filter(phone=phone).exists():
                return Response({'error': 'المستخدم موجود بالفعل'}, status=400)

            user = serializer.save()
            otp = generate_otp()
            expires_at = timezone.now() + timedelta(minutes=5)
            OTPCode.objects.create(user=user, code=otp, expires_at=expires_at)

            if user.email:
                send_otp_email(user.email, otp)
                return Response({'message': 'تم إنشاء الحساب وإرسال الرمز إلى البريد الإلكتروني'})
            else:
                #return Response({'message': f'تم إنشاء الحساب. رمز التحقق: {otp}'})
                return Response({'message': f' رمز التحقق للمشترك  صاحب الرقم ({phone}) هو {otp}'})
            
        return Response(serializer.errors, status=400)

class ResendOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({'error': 'رقم غير مسجل'}, status=404)

        last_otp = OTPCode.objects.filter(user=user).order_by('-created_at').first()
        if last_otp and (timezone.now() - last_otp.created_at).seconds < 60:
            return Response({'error': 'الرجاء الانتظار قبل إعادة الإرسال'}, status=429)

        code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=5)
        OTPCode.objects.create(user=user, code=code, expires_at=expires_at)

        if user.email:
            send_otp_email(user.email, code)
            return Response({'message': 'تم إرسال الرمز مرة أخرى للبريد'})
        else:
            return Response({'message': f' رمز التحقق الجديد  للمشترك  صاحب الرقم ({phone}) هو {code}'})
            #return Response({'message': f'رمز التحقق الجديد: {code}'})


class VerifyOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')
        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({'error': 'المستخدم غير موجود'}, status=404)

        otp_record = OTPCode.objects.filter(user=user, code=otp).order_by('-created_at').first()
        if not otp_record:
            return Response({'error': 'رمز خاطئ'}, status=400)

        if timezone.now() > otp_record.expires_at:
            return Response({'error': 'انتهت صلاحية الرمز'}, status=400)

        qr_path = generate_user_qr(user)
        qr_url = request.build_absolute_uri(qr_path)

        return Response({
            "message": "تم التحقق بنجاح",
            "qr_code_url": qr_url
        })

    


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            password = serializer.validated_data['password']
            user = User.objects.filter(phone=phone, password_hash=password).first()
            if user:
                return Response({'message': 'تم تسجيل الدخول', 'user_id': user.id})
            return Response({'error': 'بيانات الدخول غير صحيحة'}, status=401)
        return Response(serializer.errors, status=400)



class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            confirm = serializer.validated_data['confirm_password']

            if new_password != confirm:
                return Response({'error': 'كلمتا المرور غير متطابقتين'}, status=400)

            user = User.objects.filter(phone=phone).first()
            if not user:
                return Response({'error': 'المستخدم غير موجود'}, status=404)

            otp_record = OTPCode.objects.filter(user=user, code=otp).order_by('-created_at').first()
            if not otp_record or timezone.now() > otp_record.expires_at:
                return Response({'error': 'الرمز غير صالح'}, status=400)

            user.password_hash = new_password
            user.save()
            qr_path = generate_user_qr(user)
            qr_url = request.build_absolute_uri(qr_path)

            return Response({
                "message": "تم تعيين كلمة مرور جديدة",
                "qr_code_url": qr_url
            })


        return Response(serializer.errors, status=400)
    



class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user_id = request.headers.get('User-ID')
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({'error': 'مستخدم غير معروف'}, status=403)

            old = serializer.validated_data['old_password']
            new = serializer.validated_data['new_password']
            confirm = serializer.validated_data['confirm_password']

            if user.password_hash != old:
                return Response({'error': 'كلمة المرور القديمة خاطئة'}, status=400)
            if new != confirm:
                return Response({'error': 'كلمتا المرور غير متطابقتين'}, status=400)

            user.password_hash = new
            user.save()
            qr_path = generate_user_qr(user)
            qr_url = request.build_absolute_uri(qr_path)

            return Response({
                "message": "تم تغيير كلمة المرور",
                "qr_code_url": qr_url
            })

        return Response(serializer.errors, status=400)
    

@api_view(['GET'])
def check_user_subscription(request, user_id):
    now = timezone.now()
    try:
        sub = Subscription.objects.get(user_id=user_id, is_active=True, end_date__gte=now)
        return Response({
            "subscribed": True,
            "plan": sub.plan.name,
            "expires_on": sub.end_date
        })
    except Subscription.DoesNotExist:
        return Response({"subscribed": False})


@api_view(['GET'])
def get_subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    data = [
        {
            "id": plan.id,
            "name": plan.name,
            "duration_in_days": plan.duration_in_days,
            "price": plan.price
        } for plan in plans
    ]
    return Response(data)


@api_view(['POST'])
def request_subscription(request):
    user_id = request.data.get('user_id')
    plan_id = request.data.get('plan_id')

    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
        user = User.objects.get(id=user_id)
        start = timezone.now()
        end = start + timezone.timedelta(days=plan.duration_in_days)

        sub = Subscription.objects.create(
            user=user,
            plan=plan,
            start_date=start,
            end_date=end,
            is_active=False
        )

        print(f"🔔 المستخدم {user.name} ({user.phone}) طلب الاشتراك في {plan.name}. يرجى الدفع في المتجر أو للمندوب.")

        return Response({
            "message": "تم طلب الاشتراك. يرجى الدفع في المتجر أو لمندوب التوصيل.",
            "plan": plan.name,
            "price": plan.price
        })
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(['GET'])
#@permission_classes([IsAdminUser])
def list_all_users_with_subscription_status(request):
    users = User.objects.all()
    data = []
    now = timezone.now()
    for user in users:
        try:
            sub = Subscription.objects.get(user=user, is_active=True, end_date__gte=now)
            status_sub = {
                "subscribed": True,
                "plan": sub.plan.name,
                "end_date": sub.end_date
            }
        except Subscription.DoesNotExist:
            status_sub = {"subscribed": False}

        data.append({
            "user_id": user.id,
            "name": user.name,
            "phone": user.phone,
            "subscription": status_sub
        })
    return Response(data)



@api_view(['POST'])
#@permission_classes([IsAdminUser])
def activate_user_subscription(request):
    user_id = request.data.get("user_id")
    try:
        sub = Subscription.objects.filter(user_id=user_id).latest("requested_at")
        sub.is_active = True
        sub.save()

        user = sub.user
        qr_path = generate_user_qr(user)
        user.qr_code = qr_path
        user.save()

        return Response({"message": "تم تفعيل اشتراك المستخدم وتحديث QR."})
    except Subscription.DoesNotExist:
        return Response({"error": "لا يوجد اشتراك مضاف لهذا المستخدم."}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
#@permission_classes([IsAdminUser])
def create_subscription_plan(request):
    name = request.data.get('name')
    duration_in_days = request.data.get('duration_in_days')
    price = request.data.get('price')

    if not name or not duration_in_days or not price:
        return Response({"error": "جميع الحقول مطلوبة."}, status=400)

    plan = SubscriptionPlan.objects.create(
        name=name,
        duration_in_days=duration_in_days,
        price=price
    )
    return Response({"message": "تم إنشاء خطة الاشتراك.", "plan_id": plan.id})

