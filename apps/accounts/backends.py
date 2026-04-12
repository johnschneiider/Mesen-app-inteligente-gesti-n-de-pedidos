from django.contrib.auth.backends import ModelBackend
from .models import User


class PhoneBackend(ModelBackend):
    def authenticate(self, request, phone=None, password=None, **kwargs):
        if phone is None:
            phone = kwargs.get('username')
        try:
            user = User.objects.get(phone=phone)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
