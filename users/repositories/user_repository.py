from django.db.models import Q
from users.models import CustomUser

class UserRepository:
    @staticmethod
    def create_user(email: str, name: str, password: str, **extra_fields) -> CustomUser:
        user = CustomUser(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    @staticmethod
    def get_user_by_email(email: str) -> CustomUser:
        return CustomUser.objects.filter(email=email).first()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> CustomUser:
        return CustomUser.objects.filter(id=user_id).first()
    
    @staticmethod
    def search_users(query: str):
        return CustomUser.objects.filter(
            Q(email__icontains=query) |
            Q(name__icontains=query)
        )
    
    @staticmethod
    def update_user(user: CustomUser, **kwargs) -> CustomUser:
        for key, value in kwargs.items():
            setattr(user, key, value)
        user.save()
        return user
    

    @staticmethod
    def delete_user(user: CustomUser):
        user.delete()
