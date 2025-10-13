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
            # Keep a copy of primary contact email before creation
            primary_email = data.get('primary_email')

            company = service.create_company(data)

            # After successful company creation, send activation OTP to primary contact if available
            if primary_email:
                try:
                    from users.models import PasswordResetOTP
                    from users.services.email_service import email_service
                    otp_obj = PasswordResetOTP.generate_otp(primary_email, purpose='account_activation')
                    email_service.send_account_activation_otp(primary_email, otp_obj.otp, primary_email.split('@')[0])
                    return Response({
                        "message": "Activation code sent to primary contact email",
                        "primary_email": primary_email
                    }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    print(f"OTP send failed for {primary_email}: {e}")
            # Fallback if no primary email or sending failed
            return Response({
                "message": "Company created. Activation code could not be sent",
                "primary_email": primary_email
            }, status=status.HTTP_201_CREATED)
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

            # Create notifications for each user in the company
            try:
                from notifications.models import Notification
                for u in users:
                    Notification.objects.create(
                        user=u,
                        title="Company Approved",
                        message=f"Your company '{company.official_name}' has been approved. You can now publish ads and place bids.",
                        type="account",
                        priority="normal",
                        metadata={
                            "company_id": company.id,
                            "company_name": company.official_name,
                            "action_type": "company_approved"
                        }
                    )
            except Exception:
                # Non-fatal: proceed even if notification creation fails
                pass

            return Response({"message": "Company approved, permissions updated, and notifications sent."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to approve the company: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RejectCompanyView(APIView):
    """Reject a company and revoke user permissions if previously approved.

    POST /api/company/<company_id>/reject/
    Response: {"message": "Company rejected."}
    """
    permission_classes = [IsAdminUser]

    def post(self, request, company_id):
        try:
            company = service.get_company_by_id(company_id)
            if not company:
                return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

            if company.status == "rejected":
                return Response({"message": "Company is already rejected."}, status=status.HTTP_200_OK)

            # If it was approved before, remove user permissions
            was_approved = company.status == 'approved'
            company.status = "rejected"
            company.save()

            users = User.objects.filter(company=company)

            if was_approved:
                users.update(can_place_ads=False, can_place_bids=False)

            # Create notifications for each user in the company (mirrors approval flow)
            try:
                from notifications.models import Notification
                rejection_reason = request.data.get('reason') if hasattr(request, 'data') else None
                for u in users:
                    Notification.objects.create(
                        user=u,
                        title="Verification Update Needed",
                        message=(
                            f"Your company '{company.official_name}' verification was not approved. "
                            "Please review your submitted details and resubmit the required documents. "
                            "You can contact support if you need help." +
                            (f" Reason: {rejection_reason}" if rejection_reason else "")
                        ),
                        type="account",
                        priority="high",
                        metadata={
                            "company_id": company.id,
                            "company_name": company.official_name,
                            "action_type": "company_rejected",
                            "support_url": "/contact",
                            "previous_status": "approved" if was_approved else "pending",
                        }
                    )
            except Exception:
                # Non-fatal: continue even if notification creation fails
                pass

            return Response({"message": "Company rejected."}, status=status.HTTP_200_OK)
        except Exception as e:  # noqa: PIE786 (retain variable for logging if needed later)
            return Response({"error": f"Failed to reject the company: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            sector_filter = request.query_params.get('sector', 'all')
            country_filter = request.query_params.get('country', 'all')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))

            # Validate status parameter
            valid_statuses = ['all', 'pending', 'approved', 'rejected']
            if status_filter not in valid_statuses:
                return Response(
                    {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate sector parameter
            from company.models import Company
            valid_sectors = ['all'] + [choice[0] for choice in Company.SECTOR_CHOICES]
            if sector_filter not in valid_sectors:
                return Response(
                    {"error": f"Invalid sector. Must be one of: {', '.join(valid_sectors)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get filtered companies
            pagination_data = service.get_admin_companies_filtered(
                search=search,
                status=status_filter,
                sector=sector_filter,
                country=country_filter,
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
                {"error": f"Failed to retrieve companies: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanyFiltersView(APIView):
    """
    Endpoint for getting available filter options for companies
    GET /api/company/filters/
    """
    permission_classes = [AllowAny]  # Allow access for frontend to populate dropdowns

    def get(self, request):
        try:
            from company.models import Company

            # Get available sectors
            sectors = [{'value': choice[0], 'label': choice[1]} for choice in Company.SECTOR_CHOICES]

            # Get available countries (from existing companies)
            countries = Company.objects.values_list('country', flat=True).distinct().order_by('country')
            countries_list = [{'value': country, 'label': country} for country in countries if country]

            # Get available statuses
            statuses = [{'value': choice[0], 'label': choice[1]} for choice in Company.STATUS_CHOICES]

            return Response({
                'sectors': sectors,
                'countries': countries_list,
                'statuses': statuses
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to retrieve filter options"},
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
                {"error": f"Failed to retrieve company: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminCompanyStatsView(APIView):
    """
    Admin endpoint for retrieving company statistics
    GET /api/company/admin/companies/{id}/stats/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, company_id):
        try:
            from ads.models import Ad
            from bids.models import Bid
            from users.models import User

            company = service.get_company_by_id(company_id)
            if not company:
                return Response(
                    {"error": "Company not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get all users from this company
            company_users = User.objects.filter(company=company)

            # Get active ads count (ads created by users from this company)
            active_ads_count = Ad.objects.filter(
                user__in=company_users,
                is_active=True,
                is_complete=True,
            ).count()

            # Get total bids count (bids made by users from this company)
            total_bids_count = Bid.objects.filter(
                user__in=company_users
            ).count()

            # Get completed deals count (bids with status 'won')
            completed_deals_count = Bid.objects.filter(
                user__in=company_users,
                status='won'
            ).count()

            # Get additional statistics
            total_ads_count = Ad.objects.filter(
                user__in=company_users,
                is_complete=True
            ).count()

            pending_ads_count = Ad.objects.filter(
                user__in=company_users,
                is_complete=False
            ).count()

            winning_bids_count = Bid.objects.filter(
                user__in=company_users,
                status='winning'
            ).count()

            # Get recent transaction activity (last 5 completed deals)
            recent_transactions = Bid.objects.filter(
                user__in=company_users,
                status='won'
            ).select_related('ad', 'user').order_by('-updated_at')[:5]

            transaction_history = []
            for bid in recent_transactions:
                transaction_history.append({
                    'id': bid.id,
                    'ad_name': bid.ad.item_name if hasattr(bid.ad, 'item_name') else 'N/A',
                    'bid_amount': float(bid.bid_price_per_unit),
                    'volume': float(bid.volume_requested),
                    'total_value': float(bid.bid_price_per_unit * bid.volume_requested),
                    'date': bid.updated_at.isoformat(),
                    'buyer_name': bid.user.get_full_name() if bid.user.get_full_name() else bid.user.username
                })

            stats = {
                "active_ads": active_ads_count,
                "total_bids": total_bids_count,
                "completed_deals": completed_deals_count,
                "total_ads": total_ads_count,
                "pending_ads": pending_ads_count,
                "winning_bids": winning_bids_count,
                "company_id": company_id,
                "company_name": company.official_name,
                "recent_transactions": transaction_history
            }

            return Response(stats, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve company statistics: {str(e)}"},
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
                    # Send approval notifications (already handled in separate ApproveCompanyView, but keep parity)
                    try:
                        from notifications.models import Notification
                        for u in users:
                            Notification.objects.create(
                                user=u,
                                title="Company Approved",
                                message=f"Your company '{company.official_name}' has been approved. You can now publish ads and place bids.",
                                type="account",
                                priority="normal",
                                metadata={
                                    "company_id": company.id,
                                    "company_name": company.official_name,
                                    "action_type": "company_approved"
                                }
                            )
                    except Exception:
                        pass
                elif new_status == 'rejected':
                    # Send rejection notifications
                    try:
                        from notifications.models import Notification
                        users = User.objects.filter(company=company)
                        for u in users:
                            Notification.objects.create(
                                user=u,
                                title="Verification Update Needed",
                                message=(
                                    f"Your company '{company.official_name}' verification was not approved. "
                                    "Please review details and resubmit. Contact support if you need assistance."
                                ),
                                type="account",
                                priority="high",
                                metadata={
                                    "company_id": company.id,
                                    "company_name": company.official_name,
                                    "action_type": "company_rejected",
                                    "support_url": "/contact"
                                }
                            )
                    except Exception:
                        pass

            serializer = AdminCompanyDetailSerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to update company: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


