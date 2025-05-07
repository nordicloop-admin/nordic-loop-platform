from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from company.serializer import CompanySerializer
from company.repository.company_repository import CompanyRepository
from company.services.company_service import CompanyService

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
    
