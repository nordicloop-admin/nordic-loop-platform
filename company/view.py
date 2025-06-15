from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from company.serializer import CompanySerializer, CompanyAdminSerializer
from company.repository.company_repository import CompanyRepository
from company.services.company_service import CompanyService
from rest_framework.permissions import IsAdminUser
from rest_framework import viewsets, mixins, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from users.models import User 

repository = CompanyRepository()
service = CompanyService(repository)


class CompanyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Create a company
        try:
            company = service.create_company(request.data)
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class CompanyAdminViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all().order_by('-registration_date')
    serializer_class = CompanyAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['official_name', 'vat_number', 'email', 'primary_email', 'primary_first_name', 'primary_last_name']
    filterset_fields = ['status']

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'all':
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        company = self.get_object()
        status_value = request.data.get('status')
        if status_value not in dict(Company.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        company.status = status_value
        company.save()
        serializer = self.get_serializer(company)
        return Response(serializer.data)

    
