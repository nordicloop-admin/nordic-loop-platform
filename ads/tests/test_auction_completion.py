"""
Tests for AuctionCompletionService

This module contains comprehensive tests for the auction completion functionality,
including automatic closure, manual closure, and notification sending.
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from ads.models import Ad
from ads.auction_services.auction_completion import AuctionCompletionService
from bids.models import Bid
from notifications.models import Notification
from users.models import User
from categories.models import Category, Subcategory
from locations.models import Location


class AuctionCompletionServiceTest(TestCase):
    """Test cases for AuctionCompletionService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = AuctionCompletionService()
        
        # Create test users
        self.seller = User.objects.create_user(
            username='seller@test.com',
            email='seller@test.com',
            password='testpass123'
        )
        self.bidder1 = User.objects.create_user(
            username='bidder1@test.com',
            email='bidder1@test.com',
            password='testpass123'
        )
        self.bidder2 = User.objects.create_user(
            username='bidder2@test.com',
            email='bidder2@test.com',
            password='testpass123'
        )
        
        # Create test category and location
        self.category = Category.objects.create(name='Test Category')
        self.subcategory = Subcategory.objects.create(
            name='Test Subcategory',
            category=self.category
        )
        self.location = Location.objects.create(
            country='Test Country',
            city='Test City'
        )
        
        # Create test auction
        self.auction = Ad.objects.create(
            user=self.seller,
            category=self.category,
            subcategory=self.subcategory,
            location=self.location,
            title='Test Auction',
            description='Test auction description',
            available_quantity=Decimal('100.00'),
            unit_of_measurement='tons',
            starting_bid_price=Decimal('50.00'),
            currency='EUR',
            auction_duration=7,
            is_complete=True,
            is_active=True,
            auction_start_date=timezone.now() - timedelta(days=7),
            auction_end_date=timezone.now() - timedelta(minutes=10)  # Expired
        )
    
    def test_get_expired_auctions(self):
        """Test finding expired auctions"""
        expired_auctions = self.service.get_expired_auctions(grace_period_minutes=5)
        
        self.assertEqual(len(expired_auctions), 1)
        self.assertEqual(expired_auctions[0].id, self.auction.id)
    
    def test_close_auction_with_winner(self):
        """Test closing auction with a winning bid"""
        # Create winning bid
        winning_bid = Bid.objects.create(
            user=self.bidder1,
            ad=self.auction,
            bid_price_per_unit=Decimal('75.00'),
            volume_requested=Decimal('50.00'),
            status='active'
        )
        
        # Create losing bid
        losing_bid = Bid.objects.create(
            user=self.bidder2,
            ad=self.auction,
            bid_price_per_unit=Decimal('60.00'),
            volume_requested=Decimal('30.00'),
            status='active'
        )
        
        # Close auction
        result = self.service.close_auction_with_notifications(self.auction)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertTrue(result['has_winner'])
        self.assertEqual(result['winner_email'], self.bidder1.email)
        self.assertEqual(result['winning_price'], Decimal('75.00'))
        
        # Verify bid statuses
        winning_bid.refresh_from_db()
        losing_bid.refresh_from_db()
        self.assertEqual(winning_bid.status, 'won')
        self.assertEqual(losing_bid.status, 'lost')
        
        # Verify auction status
        self.auction.refresh_from_db()
        self.assertFalse(self.auction.is_active)
        self.assertEqual(self.auction.status, 'completed')
        
        # Verify notification was sent
        notifications = Notification.objects.filter(
            user=self.bidder1,
            type='auction'
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn('won', notifications.first().title.lower())
    
    def test_close_auction_without_bids(self):
        """Test closing auction with no bids"""
        result = self.service.close_auction_with_notifications(self.auction)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertFalse(result['has_winner'])
        self.assertEqual(result['message'], 'Auction closed - no bids received')
        
        # Verify auction status
        self.auction.refresh_from_db()
        self.assertFalse(self.auction.is_active)
        self.assertEqual(self.auction.status, 'completed')
    
    def test_close_auction_reserve_not_met(self):
        """Test closing auction where reserve price is not met"""
        # Set reserve price
        self.auction.reserve_price = Decimal('100.00')
        self.auction.save()
        
        # Create bid below reserve
        bid = Bid.objects.create(
            user=self.bidder1,
            ad=self.auction,
            bid_price_per_unit=Decimal('75.00'),
            volume_requested=Decimal('50.00'),
            status='active'
        )
        
        # Close auction
        result = self.service.close_auction_with_notifications(self.auction)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertFalse(result['has_winner'])
        self.assertEqual(result['message'], 'Auction closed - reserve price not met')
        self.assertEqual(result['reserve_price'], Decimal('100.00'))
        self.assertEqual(result['highest_bid'], Decimal('75.00'))
        
        # Verify bid status
        bid.refresh_from_db()
        self.assertEqual(bid.status, 'lost')
        
        # Verify auction status
        self.auction.refresh_from_db()
        self.assertFalse(self.auction.is_active)
        self.assertEqual(self.auction.status, 'completed')
    
    def test_close_auction_manually(self):
        """Test manual auction closure by admin"""
        # Create winning bid
        winning_bid = Bid.objects.create(
            user=self.bidder1,
            ad=self.auction,
            bid_price_per_unit=Decimal('75.00'),
            volume_requested=Decimal('50.00'),
            status='active'
        )
        
        # Close auction manually
        result = self.service.close_auction_manually(self.auction, winning_bid)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertTrue(result['has_winner'])
        self.assertEqual(result['winner_email'], self.bidder1.email)
        self.assertTrue(result['notification_sent'])
        
        # Verify bid status
        winning_bid.refresh_from_db()
        self.assertEqual(winning_bid.status, 'won')
        
        # Verify auction status
        self.auction.refresh_from_db()
        self.assertFalse(self.auction.is_active)
        self.assertEqual(self.auction.status, 'completed')
        
        # Verify notification was sent
        notifications = Notification.objects.filter(
            user=self.bidder1,
            type='auction'
        )
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertIn('won', notification.title.lower())
        self.assertEqual(notification.metadata['closure_type'], 'manual')
    
    @patch('ads.services.auction_completion.logging_service')
    def test_error_handling(self, mock_logging):
        """Test error handling in auction closure"""
        # Create invalid auction (no end date)
        invalid_auction = Ad.objects.create(
            user=self.seller,
            category=self.category,
            title='Invalid Auction',
            is_complete=True,
            is_active=True,
            auction_end_date=None  # Invalid
        )
        
        result = self.service.close_auction_with_notifications(invalid_auction)
        
        # Should handle error gracefully
        self.assertFalse(result['success'])
        self.assertIn('Error closing auction', result['message'])
        
        # Should log error
        mock_logging.log_error.assert_called()
    
    def test_notification_metadata(self):
        """Test that notification metadata is properly set"""
        # Create winning bid
        winning_bid = Bid.objects.create(
            user=self.bidder1,
            ad=self.auction,
            bid_price_per_unit=Decimal('75.00'),
            volume_requested=Decimal('50.00'),
            status='active'
        )
        
        # Close auction
        self.service.close_auction_with_notifications(self.auction)
        
        # Check notification metadata
        notification = Notification.objects.filter(
            user=self.bidder1,
            type='auction'
        ).first()
        
        self.assertIsNotNone(notification)
        metadata = notification.metadata
        
        self.assertEqual(metadata['auction_id'], self.auction.id)
        self.assertEqual(metadata['bid_id'], winning_bid.id)
        self.assertEqual(metadata['winning_price'], '75.00')
        self.assertEqual(metadata['volume'], '50.00')
        self.assertEqual(metadata['currency'], 'EUR')
        self.assertEqual(metadata['unit'], 'tons')
        self.assertEqual(metadata['action_type'], 'auction_won')
        self.assertEqual(metadata['closure_type'], 'automatic')


class BidSignalsTest(TestCase):
    """Test cases for bid signals and notifications"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.seller = User.objects.create_user(
            username='seller@test.com',
            email='seller@test.com',
            password='testpass123'
        )
        self.bidder = User.objects.create_user(
            username='bidder@test.com',
            email='bidder@test.com',
            password='testpass123'
        )

        # Create test category and location
        self.category = Category.objects.create(name='Test Category')
        self.location = Location.objects.create(
            country='Test Country',
            city='Test City'
        )

        # Create test auction
        self.auction = Ad.objects.create(
            user=self.seller,
            category=self.category,
            location=self.location,
            title='Test Auction',
            description='Test auction description',
            available_quantity=Decimal('100.00'),
            unit_of_measurement='tons',
            starting_bid_price=Decimal('50.00'),
            currency='EUR',
            is_complete=True,
            is_active=True,
            auction_start_date=timezone.now(),
            auction_end_date=timezone.now() + timedelta(days=7)
        )

    def test_winner_notification_signal(self):
        """Test that winner notification is sent via signal"""
        # Create bid
        bid = Bid.objects.create(
            user=self.bidder,
            ad=self.auction,
            bid_price_per_unit=Decimal('75.00'),
            volume_requested=Decimal('50.00'),
            status='active'
        )

        # Change status to won (should trigger signal)
        bid.status = 'won'
        bid.save()

        # Check that notification was created
        notifications = Notification.objects.filter(
            user=self.bidder,
            type='auction',
            metadata__action_type='auction_won'
        )
        self.assertEqual(notifications.count(), 1)

        notification = notifications.first()
        self.assertIn('won', notification.title.lower())
        self.assertEqual(notification.metadata['bid_id'], bid.id)

    def test_outbid_notification_signal(self):
        """Test that outbid notification is sent via signal"""
        # Create bid
        bid = Bid.objects.create(
            user=self.bidder,
            ad=self.auction,
            bid_price_per_unit=Decimal('75.00'),
            volume_requested=Decimal('50.00'),
            status='active'
        )

        # Change status to outbid (should trigger signal)
        bid.status = 'outbid'
        bid.save()

        # Check that notification was created
        notifications = Notification.objects.filter(
            user=self.bidder,
            type='bid',
            metadata__action_type='outbid'
        )
        self.assertEqual(notifications.count(), 1)

        notification = notifications.first()
        self.assertIn('outbid', notification.title.lower())
        self.assertEqual(notification.metadata['bid_id'], bid.id)

    def test_no_duplicate_notifications(self):
        """Test that duplicate notifications are not created"""
        # Create bid
        bid = Bid.objects.create(
            user=self.bidder,
            ad=self.auction,
            bid_price_per_unit=Decimal('75.00'),
            volume_requested=Decimal('50.00'),
            status='active'
        )

        # Change to won twice
        bid.status = 'won'
        bid.save()

        bid.status = 'won'  # Same status
        bid.save()

        # Should only have one notification
        notifications = Notification.objects.filter(
            user=self.bidder,
            type='auction',
            metadata__action_type='auction_won'
        )
        self.assertEqual(notifications.count(), 1)
