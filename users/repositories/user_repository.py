from django.db.models import Q
from users.models import CustomUser
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService

logging_service = LoggingService()


class UserRepository:
    """
    A class to manage CRUD operations for User
    """

    def create_user(self, email, name, password, **extra_fields) -> RepositoryResponse:
        """
        Creates a new user
        """
        try:
            user = CustomUser(email=email, name=name, **extra_fields)
            user.set_password(password)
            user.save()
            return RepositoryResponse(
                success=True,
                message="User created successfully",
                data=user,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to create user",
                data=None,
            )

    def get_user_by_email(self, email) -> RepositoryResponse:
        """
        Get a user by email
        """
        try:
            user = CustomUser.objects.get(email=email)
            return RepositoryResponse(
                success=True,
                message="User found",
                data=user,
            )
        except CustomUser.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="User not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get user",
                data=None,
            )

    def get_user_by_id(self, id) -> RepositoryResponse:
        """
        Get a user by ID
        """
        try:
            user = CustomUser.objects.get(id=id)
            return RepositoryResponse(
                success=True,
                message="User found",
                data=user,
            )
        except CustomUser.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="User not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get user",
                data=None,
            )

    def search_users(self, query) -> RepositoryResponse:
        """
        Search for users by email or name
        """
        try:
            users = CustomUser.objects.filter(
                Q(email__icontains=query) |
                Q(name__icontains=query)
            )
            return RepositoryResponse(
                success=True,
                message="Users found",
                data=users,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to search users",
                data=None,
            )

    def update_user(self, id, data) -> RepositoryResponse:
        """
        Update a user with the provided data
        """
        try:
            user = CustomUser.objects.get(id=id)
            for key, value in data.items():
                if key == 'password':
                    user.set_password(value)
                else:
                    setattr(user, key, value)
            user.save()
            return RepositoryResponse(
                success=True,
                message="User updated successfully",
                data=user,
            )
        except CustomUser.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="User not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to update user",
                data=None,
            )

    def delete_user(self, id) -> RepositoryResponse:
        """
        Delete a user
        """
        try:
            user = CustomUser.objects.get(id=id)
            user.delete()
            return RepositoryResponse(
                success=True,
                message="User deleted successfully",
                data=None,
            )
        except CustomUser.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="User not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to delete user",
                data=None,
            )
