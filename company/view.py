from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from company.serializer import CompanySerializer, AdminCompanyListSerializer, AdminCompanyDetailSerializer
from company.repository.company_repository import CompanyRepository
from company.services.company_service import CompanyService
from rest_framework.permissions import IsAdminUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from users.models import User

repository = CompanyRepository()
service = CompanyService(repository)


@method_decorator(csrf_exempt, name='dispatch')
class CompanyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Create a company
        try:
            # Get data from request - handle both JSON and form data
            if hasattr(request, 'data'):
                data = request.data
            else:
                # For non-DRF requests
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except:
                    data = request.POST

            company = service.create_company(data)
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Better error logging for debugging
            import traceback
            error_details = {
                "error": "Something went wrong",
                "details": str(e),
                "traceback": traceback.format_exc()
            }
            return Response(error_details, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, company_id=None, vat=None):
        # Retrieve a company by ID or VAT or list all
        try:
            if company_id:
                company = service.get_company_by_id(company_id)
                if not company:
                    return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = CompanySerializer(company)
                return Response(serializer.data)

            elif vat:
                company = service.get_company_by_vat(vat)
                if not company:
                    return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = CompanySerializer(company)
                return Response(serializer.data)

            else:
                companies = service.list_companies()
                serializer = CompanySerializer(companies, many=True)
                return Response(serializer.data)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, company_id):
        # Update a company
        try:
            company = service.get_company_by_id(company_id)
            if not company:
                return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
            updated_company = service.update_company(company_id, request.data)
            serializer = CompanySerializer(updated_company)
            return Response(serializer.data)
        except Exception:
            return Response({"error": "Update failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, company_id):
        # Delete a company
        try:
            company = service.get_company_by_id(company_id)
            if not company:
                return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
            service.delete_company(company)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"error": "Delete failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def list_companies(self):
        try:
            companies = service.list_companies()
            serializer = CompanySerializer(companies, many=True)
            return Response(serializer.data)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApproveCompanyView(APIView):
    permission_classes = [IsAdminUser]  

    def post(self, request, company_id):
        try:
            company = service.get_company_by_id(company_id)
            if not company:
                return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

            if company.status == "approved":
                return Response({"message": "Company is already approved."}, status=status.HTTP_200_OK)

            company.status = "approved"
            company.save()

            users = User.objects.filter(company=company)
            users.update(can_place_ads=True, can_place_bids=True)

            return Response({"message": "Company approved and user permissions updated."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to approve the company: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminCompanyListView(APIView):
    """
    Admin endpoint for listing companies with filtering and pagination
    GET /api/company/admin/companies/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get query parameters
            search = request.query_params.get('search', None)
            status_filter = request.query_params.get('status', 'all')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))

            # Validate status parameter
            valid_statuses = ['all', 'pending', 'approved', 'rejected']
            if status_filter not in valid_statuses:
                return Response(
                    {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get filtered companies
            pagination_data = service.get_admin_companies_filtered(
                search=search,
                status=status_filter,
                page=page,
                page_size=page_size
            )

            # Serialize the results
            serializer = AdminCompanyListSerializer(pagination_data['results'], many=True)
            
            # Format response according to specification
            response_data = {
                "count": pagination_data['count'],
                "next": pagination_data['next'],
                "previous": pagination_data['previous'],
                "results": serializer.data,
                "page_size": pagination_data['page_size'],
                "total_pages": pagination_data['total_pages'],
                "current_page": pagination_data['current_page']
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Failed to retrieve companies"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminCompanyDetailView(APIView):
    """
    Admin endpoint for retrieving a specific company
    GET /api/company/admin/companies/{id}/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, company_id):
        try:
            company = service.get_company_by_id(company_id)
            if not company:
                return Response(
                    {"error": "Company not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = AdminCompanyDetailSerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to retrieve company"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, company_id):
        try:
            company = service.get_company_by_id(company_id)
            if not company:
                return Response(
                    {"error": "Company not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Update company status
            new_status = request.data.get('status')
            if new_status and new_status in ['pending', 'approved', 'rejected']:
                company.status = new_status
                company.save()

                # If approving company, update user permissions
                if new_status == 'approved':
                    users = User.objects.filter(company=company)
                    users.update(can_place_ads=True, can_place_bids=True)

            serializer = AdminCompanyDetailSerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to update company"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


