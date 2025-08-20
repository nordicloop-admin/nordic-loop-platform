"""
Bank Account Verification Service
Provides utilities for managing and explaining the verification process
"""

from typing import Dict, Any, Optional
from django.utils import timezone
from datetime import timedelta
import logging

from .models import StripeAccount
from .services import StripeConnectService

logger = logging.getLogger(__name__)


class VerificationService:
    """
    Service for managing bank account verification process
    """
    
    def __init__(self):
        self.stripe_service = StripeConnectService()
    
    def get_verification_status(self, user) -> Dict[str, Any]:
        """
        Get comprehensive verification status for a user
        """
        try:
            stripe_account = StripeAccount.objects.get(user=user)
            
            # Calculate time since submission
            time_since_submission = timezone.now() - stripe_account.created_at
            days_since_submission = time_since_submission.days
            
            # Determine expected completion time
            expected_completion = stripe_account.created_at + timedelta(days=2)
            is_overdue = timezone.now() > expected_completion
            
            status_info = self._get_detailed_status_info(
                stripe_account.account_status,
                days_since_submission,
                is_overdue
            )
            
            return {
                'success': True,
                'has_account': True,
                'account_status': stripe_account.account_status,
                'charges_enabled': stripe_account.charges_enabled,
                'payouts_enabled': stripe_account.payouts_enabled,
                'days_since_submission': days_since_submission,
                'is_overdue': is_overdue,
                'expected_completion': expected_completion,
                'status_info': status_info,
                'bank_name': stripe_account.bank_name,
                'bank_last4': stripe_account.bank_account_last4,
                'created_at': stripe_account.created_at,
                'updated_at': stripe_account.updated_at
            }
            
        except StripeAccount.DoesNotExist:
            return {
                'success': True,
                'has_account': False,
                'message': 'No payment account found. Set up your bank account to start receiving payments.'
            }
        except Exception as e:
            logger.error(f"Error getting verification status for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'Error retrieving verification status'
            }
    
    def _get_detailed_status_info(self, status: str, days_since: int, is_overdue: bool) -> Dict[str, Any]:
        """
        Get detailed status information with explanations
        """
        base_info = {
            'timeline': self._get_verification_timeline(status, days_since),
            'next_steps': self._get_next_steps(status, is_overdue),
            'why_required': self._get_verification_explanation(),
        }
        
        if status == 'active':
            return {
                **base_info,
                'title': 'Account Verified & Active',
                'description': 'Your payment account is fully verified and ready to receive payments.',
                'color': 'green',
                'can_receive_payments': True
            }
        elif status == 'pending':
            return {
                **base_info,
                'title': 'Verification in Progress',
                'description': f'Your account has been submitted for verification {days_since} day(s) ago. Stripe is reviewing your information.',
                'color': 'yellow',
                'can_receive_payments': False
            }
        elif status == 'restricted':
            return {
                **base_info,
                'title': 'Additional Information Required',
                'description': 'Stripe needs additional information to complete your verification. Check your email for instructions.',
                'color': 'red',
                'can_receive_payments': False
            }
        elif status == 'inactive':
            return {
                **base_info,
                'title': 'Account Inactive',
                'description': 'Your account is currently inactive. Contact support for assistance.',
                'color': 'gray',
                'can_receive_payments': False
            }
        else:
            return {
                **base_info,
                'title': 'Verification Starting',
                'description': 'Your bank account information has been submitted and verification is beginning.',
                'color': 'blue',
                'can_receive_payments': False
            }
    
    def _get_verification_timeline(self, status: str, days_since: int) -> Dict[str, Any]:
        """
        Get verification timeline information
        """
        if status == 'active':
            return {
                'completed': True,
                'completion_time': f'Completed after {days_since} day(s)',
                'message': 'Verification completed successfully'
            }
        elif days_since == 0:
            return {
                'completed': False,
                'expected_days': '1-2 business days',
                'message': 'Verification just started'
            }
        elif days_since <= 2:
            return {
                'completed': False,
                'expected_days': f'{2 - days_since} more day(s)',
                'message': 'Verification in normal timeframe'
            }
        else:
            return {
                'completed': False,
                'expected_days': 'Overdue',
                'message': 'Verification is taking longer than expected. Consider contacting support.'
            }
    
    def _get_next_steps(self, status: str, is_overdue: bool) -> list:
        """
        Get next steps for the user based on status
        """
        if status == 'active':
            return [
                'Your account is ready to receive payments',
                'You can now sell materials and receive payments from winning bids',
                'Check your email for payout schedule information'
            ]
        elif status == 'pending':
            if is_overdue:
                return [
                    'Verification is taking longer than expected',
                    'Check your email for any requests from Stripe',
                    'Contact support if you haven\'t heard anything in 5+ business days'
                ]
            else:
                return [
                    'Wait for Stripe to complete the verification process',
                    'Check your email regularly for any updates',
                    'No action required from you at this time'
                ]
        elif status == 'restricted':
            return [
                'Check your email for specific requirements from Stripe',
                'Provide any additional documentation requested',
                'Contact support if you need help understanding the requirements'
            ]
        elif status == 'inactive':
            return [
                'Contact Nordic Loop support immediately',
                'Provide your account details for investigation',
                'Do not create a new account - we can help reactivate this one'
            ]
        else:
            return [
                'Your information has been submitted to Stripe',
                'Verification will begin shortly',
                'You will receive email updates on progress'
            ]
    
    def _get_verification_explanation(self) -> Dict[str, Any]:
        """
        Explain why verification is required
        """
        return {
            'title': 'Why is verification required?',
            'reasons': [
                {
                    'category': 'Legal Compliance',
                    'description': 'Swedish and EU financial regulations require identity verification for all payment processors'
                },
                {
                    'category': 'Fraud Prevention',
                    'description': 'Verification protects both buyers and sellers from fraudulent transactions'
                },
                {
                    'category': 'Platform Security',
                    'description': 'Ensures all marketplace participants are legitimate businesses or individuals'
                },
                {
                    'category': 'Tax Compliance',
                    'description': 'Required for proper tax reporting and compliance with Swedish tax authorities'
                }
            ],
            'processor_note': 'Verification is handled by Stripe, our secure payment processor, not by Nordic Loop directly.'
        }
    
    def refresh_account_status(self, user) -> Dict[str, Any]:
        """
        Refresh account status from Stripe
        """
        try:
            stripe_account = StripeAccount.objects.get(user=user)
            result = self.stripe_service.update_account_status(stripe_account.stripe_account_id)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Account status updated',
                    'account_status': result['account_status'],
                    'charges_enabled': result['charges_enabled'],
                    'payouts_enabled': result['payouts_enabled']
                }
            else:
                return result
                
        except StripeAccount.DoesNotExist:
            return {
                'success': False,
                'message': 'No payment account found'
            }
        except Exception as e:
            logger.error(f"Error refreshing account status for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'Error refreshing account status'
            }
    
    def get_verification_faq(self) -> Dict[str, Any]:
        """
        Get frequently asked questions about verification
        """
        return {
            'faqs': [
                {
                    'question': 'How long does verification take?',
                    'answer': 'Typically 1-2 business days, but can take up to 5 business days in some cases.'
                },
                {
                    'question': 'What information does Stripe verify?',
                    'answer': 'Stripe verifies your identity, bank account ownership, and business information to comply with financial regulations.'
                },
                {
                    'question': 'Can I sell before verification is complete?',
                    'answer': 'You can list materials for sale, but you cannot receive payments until verification is complete.'
                },
                {
                    'question': 'What if verification is taking too long?',
                    'answer': 'Check your email for any requests from Stripe. If it\'s been more than 5 business days, contact support.'
                },
                {
                    'question': 'Is my information secure?',
                    'answer': 'Yes, all verification is handled by Stripe using bank-level security. Nordic Loop never stores your sensitive financial information.'
                }
            ]
        }
