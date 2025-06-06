from django.test import TestCase
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Bid, BidHistory
from .services import BidService
from .repository import BidRepository
from ads.models import Ad, Location
from category.models import Category, SubCategory
from company.models import Company

User = get_user_model()


class BidModelTest(TestCase):
    """Test the Bid and BidHistory models"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='bidder1',
            email='bidder1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='seller1',
            email='seller1@test.com',
            password='testpass123'
        )
        
        # Create company with correct fields
        self.company = Company.objects.create(
            official_name="Test Company",
            vat_number="12345678",
            email="test@company.com",
            country="Sweden",
            primary_email="primary@company.com"
        )
        
        # Create category
        self.category = Category.objects.create(name="Plastics")
        self.subcategory = SubCategory.objects.create(
            name="HDPE",
            category=self.category
        )
        
        # Create location
        self.location = Location.objects.create(
            country="Sweden",
            city="Stockholm",
            postal_code="11122"
        )
        
        # Create ad
        self.ad = Ad.objects.create(
            user=self.user2,
            category=self.category,
            subcategory=self.subcategory,
            location=self.location,
            title="Test HDPE Material",
            description="High quality HDPE",
            available_quantity=Decimal('100.00'),
            starting_bid_price=Decimal('50.00'),
            currency='EUR',
            unit_of_measurement='tons',
            minimum_order_quantity=Decimal('1.00'),
            is_complete=True,
            is_active=True
        )

    def test_bid_creation(self):
        """Test creating a valid bid"""
        bid = Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        self.assertEqual(bid.user, self.user1)
        self.assertEqual(bid.ad, self.ad)
        self.assertEqual(bid.bid_price_per_unit, Decimal('55.00'))
        self.assertEqual(bid.volume_requested, Decimal('10.00'))
        self.assertEqual(bid.total_bid_value, Decimal('550.00'))
        self.assertEqual(bid.status, 'active')

    def test_bid_validation_own_ad(self):
        """Test that users cannot bid on their own ads"""
        with self.assertRaises(Exception):
            Bid.objects.create(
                user=self.user2,  # Same user as ad owner
                ad=self.ad,
                bid_price_per_unit=Decimal('55.00'),
                volume_requested=Decimal('10.00')
            )

    def test_bid_validation_minimum_price(self):
        """Test bid price validation against starting price"""
        with self.assertRaises(Exception):
            Bid.objects.create(
                user=self.user1,
                ad=self.ad,
                bid_price_per_unit=Decimal('40.00'),  # Below starting price
                volume_requested=Decimal('10.00')
            )

    def test_bid_validation_volume_limits(self):
        """Test volume validation"""
        with self.assertRaises(Exception):
            Bid.objects.create(
                user=self.user1,
                ad=self.ad,
                bid_price_per_unit=Decimal('55.00'),
                volume_requested=Decimal('150.00')  # Exceeds available quantity
            )

    def test_bid_is_winning_property(self):
        """Test the is_winning property"""
        bid1 = Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00'),
            status='winning'
        )
        
        # Create another user for second bid
        user3 = User.objects.create_user(
            username='bidder2',
            email='bidder2@test.com',
            password='testpass123'
        )
        
        bid2 = Bid.objects.create(
            user=user3,
            ad=self.ad,
            bid_price_per_unit=Decimal('50.00'),
            volume_requested=Decimal('5.00'),
            status='outbid'
        )
        
        self.assertTrue(bid1.is_winning)
        self.assertFalse(bid2.is_winning)

    def test_bid_rank_property(self):
        """Test the rank property"""
        # Create another user
        user3 = User.objects.create_user(
            username='bidder2',
            email='bidder2@test.com',
            password='testpass123'
        )
        
        bid1 = Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('60.00'),
            volume_requested=Decimal('10.00'),
            status='winning'
        )
        
        bid2 = Bid.objects.create(
            user=user3,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('5.00'),
            status='outbid'
        )
        
        self.assertEqual(bid1.rank, 1)  # Highest bid
        self.assertEqual(bid2.rank, 2)  # Second highest


class BidServiceTest(TestCase):
    """Test the BidService business logic"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='bidder1',
            email='bidder1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='seller1',
            email='seller1@test.com',
            password='testpass123'
        )
        
        # Create company with correct fields
        self.company = Company.objects.create(
            official_name="Test Company",
            vat_number="12345678",
            email="test@company.com",
            country="Sweden",
            primary_email="primary@company.com"
        )
        
        # Create category
        self.category = Category.objects.create(name="Plastics")
        self.subcategory = SubCategory.objects.create(
            name="HDPE",
            category=self.category
        )
        
        # Create location
        self.location = Location.objects.create(
            country="Sweden",
            city="Stockholm",
            postal_code="11122"
        )
        
        # Create ad
        self.ad = Ad.objects.create(
            user=self.user2,
            category=self.category,
            subcategory=self.subcategory,
            location=self.location,
            title="Test HDPE Material",
            description="High quality HDPE",
            available_quantity=Decimal('100.00'),
            starting_bid_price=Decimal('50.00'),
            currency='EUR',
            unit_of_measurement='tons',
            minimum_order_quantity=Decimal('1.00'),
            is_complete=True,
            is_active=True
        )
        
        self.repository = BidRepository()
        self.service = BidService(self.repository)

    def test_create_bid_success(self):
        """Test successful bid creation"""
        bid = self.service.create_bid(
            ad_id=self.ad.id,
            bid_price_per_unit=55.00,
            volume_requested=10.00,
            user=self.user1
        )
        
        self.assertEqual(bid.bid_price_per_unit, Decimal('55.00'))
        self.assertEqual(bid.volume_requested, Decimal('10.00'))
        self.assertEqual(bid.status, 'active')

    def test_create_bid_on_own_ad_fails(self):
        """Test that users cannot bid on their own ads"""
        with self.assertRaises(ValueError) as context:
            self.service.create_bid(
                ad_id=self.ad.id,
                bid_price_per_unit=55.00,
                volume_requested=10.00,
                user=self.user2  # Ad owner
            )
        
        self.assertIn("cannot bid on your own ad", str(context.exception))

    def test_create_bid_below_starting_price_fails(self):
        """Test bid below starting price fails"""
        with self.assertRaises(ValueError) as context:
            self.service.create_bid(
                ad_id=self.ad.id,
                bid_price_per_unit=40.00,  # Below starting price
                volume_requested=10.00,
                user=self.user1
            )
        
        self.assertIn("must be at least", str(context.exception))

    def test_update_bid_success(self):
        """Test successful bid update"""
        # First create a bid
        bid = self.service.create_bid(
            ad_id=self.ad.id,
            bid_price_per_unit=55.00,
            volume_requested=10.00,
            user=self.user1
        )
        
        # Update the bid
        result = self.service.update_bid(
            bid_id=bid.id,
            bid_price_per_unit=60.00,
            user=self.user1
        )
        
        self.assertNotIn("error", result)
        self.assertEqual(result["bid"].bid_price_per_unit, Decimal('60.00'))

    def test_get_bid_statistics(self):
        """Test bid statistics calculation"""
        # Create multiple bids
        user3 = User.objects.create_user(
            username='bidder2',
            email='bidder2@test.com',
            password='testpass123'
        )
        
        Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00'),
            status='winning'
        )
        
        Bid.objects.create(
            user=user3,
            ad=self.ad,
            bid_price_per_unit=Decimal('52.00'),
            volume_requested=Decimal('5.00'),
            status='outbid'
        )
        
        stats = self.service.get_bid_statistics(self.ad.id)
        
        self.assertEqual(stats['total_bids'], 2)
        self.assertEqual(stats['highest_bid'], Decimal('55.00'))
        self.assertEqual(stats['lowest_bid'], Decimal('52.00'))
        self.assertEqual(stats['unique_bidders'], 2)


class BidAPITest(APITestCase):
    """Test the Bid API endpoints"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='bidder1',
            email='bidder1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='seller1',
            email='seller1@test.com',
            password='testpass123'
        )
        
        # Create company with correct fields
        self.company = Company.objects.create(
            official_name="Test Company",
            vat_number="12345678",
            email="test@company.com",
            country="Sweden",
            primary_email="primary@company.com"
        )
        
        # Create category
        self.category = Category.objects.create(name="Plastics")
        self.subcategory = SubCategory.objects.create(
            name="HDPE",
            category=self.category
        )
        
        # Create location
        self.location = Location.objects.create(
            country="Sweden",
            city="Stockholm",
            postal_code="11122"
        )
        
        # Create ad
        self.ad = Ad.objects.create(
            user=self.user2,
            category=self.category,
            subcategory=self.subcategory,
            location=self.location,
            title="Test HDPE Material",
            description="High quality HDPE",
            available_quantity=Decimal('100.00'),
            starting_bid_price=Decimal('50.00'),
            currency='EUR',
            unit_of_measurement='tons',
            minimum_order_quantity=Decimal('1.00'),
            is_complete=True,
            is_active=True
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)

    def test_create_bid_api(self):
        """Test creating a bid via API"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        data = {
            'ad': self.ad.id,
            'bid_price_per_unit': '55.00',
            'volume_requested': '10.00',
            'volume_type': 'partial',
            'notes': 'Test bid'
        }
        
        response = self.client.post('/api/bids/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('bid', response.data)

    def test_create_bid_unauthenticated(self):
        """Test creating a bid without authentication fails"""
        data = {
            'ad': self.ad.id,
            'bid_price_per_unit': '55.00',
            'volume_requested': '10.00'
        }
        
        response = self.client.post('/api/bids/create/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_ad_bids(self):
        """Test getting bids for an ad"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a bid first
        Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        response = self.client.get(f'/api/bids/ad/{self.ad.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('bid_statistics', response.data)

    def test_get_user_bids(self):
        """Test getting user's own bids"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a bid first
        Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        response = self.client.get('/api/bids/user/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_update_bid_api(self):
        """Test updating a bid via API"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a bid first
        bid = Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        data = {
            'bid_price_per_unit': '60.00',
            'notes': 'Updated bid'
        }
        
        response = self.client.put(f'/api/bids/{bid.id}/update/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('bid', response.data)

    def test_delete_bid_api(self):
        """Test deleting a bid via API"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a bid first
        bid = Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        response = self.client.delete(f'/api/bids/{bid.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check bid is marked as cancelled
        bid.refresh_from_db()
        self.assertEqual(bid.status, 'cancelled')

    def test_bid_search_api(self):
        """Test bid search functionality"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a bid first
        Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        response = self.client.get('/api/bids/search/?min_price=50&max_price=60')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_bid_statistics_api(self):
        """Test bid statistics endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create multiple bids
        user3 = User.objects.create_user(
            username='bidder2',
            email='bidder2@test.com',
            password='testpass123'
        )
        
        Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        Bid.objects.create(
            user=user3,
            ad=self.ad,
            bid_price_per_unit=Decimal('52.00'),
            volume_requested=Decimal('5.00')
        )
        
        response = self.client.get(f'/api/bids/ad/{self.ad.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_bids', response.data)
        self.assertIn('highest_bid', response.data)


class BidHistoryTest(TestCase):
    """Test bid history functionality"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='bidder1',
            email='bidder1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='seller1',
            email='seller1@test.com',
            password='testpass123'
        )
        
        # Create company with correct fields
        self.company = Company.objects.create(
            official_name="Test Company",
            vat_number="12345678",
            email="test@company.com",
            country="Sweden",
            primary_email="primary@company.com"
        )
        
        # Create category
        self.category = Category.objects.create(name="Plastics")
        self.subcategory = SubCategory.objects.create(
            name="HDPE",
            category=self.category
        )
        
        # Create location
        self.location = Location.objects.create(
            country="Sweden",
            city="Stockholm",
            postal_code="11122"
        )
        
        # Create ad
        self.ad = Ad.objects.create(
            user=self.user2,
            category=self.category,
            subcategory=self.subcategory,
            location=self.location,
            title="Test HDPE Material",
            description="High quality HDPE",
            available_quantity=Decimal('100.00'),
            starting_bid_price=Decimal('50.00'),
            currency='EUR',
            unit_of_measurement='tons',
            minimum_order_quantity=Decimal('1.00'),
            is_complete=True,
            is_active=True
        )

    def test_bid_history_creation(self):
        """Test that bid history is created on bid updates"""
        bid = Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        # Create history entry
        history = BidHistory.objects.create(
            bid=bid,
            previous_price=None,
            new_price=Decimal('55.00'),
            previous_volume=None,
            new_volume=Decimal('10.00'),
            change_reason='bid_placed'
        )
        
        self.assertEqual(history.bid, bid)
        self.assertEqual(history.new_price, Decimal('55.00'))
        self.assertEqual(history.change_reason, 'bid_placed')

    def test_bid_history_on_update(self):
        """Test history creation on bid update"""
        bid = Bid.objects.create(
            user=self.user1,
            ad=self.ad,
            bid_price_per_unit=Decimal('55.00'),
            volume_requested=Decimal('10.00')
        )
        
        # Update bid
        previous_price = bid.bid_price_per_unit
        bid.bid_price_per_unit = Decimal('60.00')
        bid.save()
        
        # Create history entry
        BidHistory.objects.create(
            bid=bid,
            previous_price=previous_price,
            new_price=bid.bid_price_per_unit,
            previous_volume=bid.volume_requested,
            new_volume=bid.volume_requested,
            change_reason='bid_updated'
        )
        
        history_entries = BidHistory.objects.filter(bid=bid)
        self.assertEqual(history_entries.count(), 1)
        
        latest_history = history_entries.first()
        self.assertEqual(latest_history.previous_price, Decimal('55.00'))
        self.assertEqual(latest_history.new_price, Decimal('60.00'))
        self.assertEqual(latest_history.change_reason, 'bid_updated')
