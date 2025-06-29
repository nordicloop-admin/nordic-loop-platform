from django.db.models import Q
from django.core.paginator import Paginator
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from users.models import User

logging_service = LoggingService()


class UserRepository:
    
    def get_user_by_id(self, user_id) -> RepositoryResponse:
        """Get a user by ID"""
        try:
            user = User.objects.select_related('company').get(id=user_id)
            return RepositoryResponse(
                success=True,
                message="User found",
                data=user,
            )
        except User.DoesNotExist:
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

    def get_admin_users_filtered(self, search=None, company=None, is_active=None, page=1, page_size=10) -> RepositoryResponse:
        """
        Get users for admin with filtering and pagination support
        """
        try:
            queryset = User.objects.select_related('company').all().order_by('-date_joined')
            
            # Apply search filter
            if search:
                queryset = queryset.filter(
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(username__icontains=search) |
                    Q(company__official_name__icontains=search)
                )
            
            # Apply company filter
            if company:
                try:
                    company_id = int(company)
                    queryset = queryset.filter(company_id=company_id)
                except (ValueError, TypeError):
                    # If company is not a valid integer, try to filter by company name
                    queryset = queryset.filter(company__official_name__icontains=company)
            
            # Apply is_active filter
            if is_active is not None:
                if isinstance(is_active, str):
                    is_active = is_active.lower() in ['true', '1', 'yes', 'active']
                queryset = queryset.filter(is_active=is_active)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            
            try:
                users_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                users_page = paginator.page(1)
            
            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': users_page.number,
                'page_size': page_size,
                'next': users_page.has_next(),
                'previous': users_page.has_previous(),
                'results': list(users_page.object_list)
            }
            
            return RepositoryResponse(
                success=True,
                message="Users retrieved successfully",
                data=pagination_data,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get users",
                data=None,
            )

    def list_users(self) -> RepositoryResponse:
        """List all users"""
        try:
            users = User.objects.select_related('company').all()
            return RepositoryResponse(
                success=True,
                message="Users found",
                data=users,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get users",
                data=None,
            )

    def create_user(self, data) -> RepositoryResponse:
        """Create a new user"""
        try:
            user = User.objects.create_user(**data)
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

    def update_user(self, user_id, data) -> RepositoryResponse:
        """Update a user"""
        try:
            user = User.objects.get(id=user_id)
            for key, value in data.items():
                setattr(user, key, value)
            user.save()
            return RepositoryResponse(
                success=True,
                message="User updated successfully",
                data=user,
            )
        except User.DoesNotExist:
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

    def delete_user(self, user_id) -> RepositoryResponse:
        """Delete a user"""
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return RepositoryResponse(
                success=True,
                message="User deleted successfully",
                data=None,
            )
        except User.DoesNotExist:
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