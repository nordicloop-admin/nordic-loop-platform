from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from ads.models import Ad, Location
from category.models import Category, SubCategory, CategorySpecification
from ads.serializer import AdStep1Serializer, AdStep8Serializer

User = get_user_model()


class AdModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.category = Category.objects.create(name="Plastics")
        self.subcategory = SubCategory.objects.create(
            name="PP", 
            category=self.category
        )

    def test_ad_creation(self):
        """Test basic ad creation"""
        ad = Ad.objects.create(
            user=self.user,
            current_step=1,
            is_complete=False
        )
        self.assertEqual(ad.current_step, 1)
        self.assertFalse(ad.is_complete)
        self.assertEqual(str(ad), f"Ad #{ad.id}")

    def test_step_completion_status(self):
        """Test step completion status tracking"""
        ad = Ad.objects.create(
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            packaging='octabin',
            material_frequency='quarterly'
        )
        
        status = ad.get_step_completion_status()
        self.assertTrue(status[1])  # Step 1 should be complete
        self.assertFalse(status[2])  # Step 2 should be incomplete

    def test_total_starting_value_calculation(self):
        """Test total starting value calculation"""
        ad = Ad.objects.create(
            user=self.user,
            available_quantity=100,
            starting_bid_price=29.50
        )
        self.assertEqual(ad.total_starting_value, 2950.00)


class LocationModelTest(TestCase):
    def test_location_creation(self):
        """Test location model creation"""
        location = Location.objects.create(
            country="Sweden",
            city="Stockholm",
            state_province="Stockholm County"
        )
        self.assertEqual(str(location), "Stockholm, Stockholm County, Sweden")


class AdAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.category = Category.objects.create(name="Plastics")
        self.subcategory = SubCategory.objects.create(
            name="PP", 
            category=self.category
        )
        self.client.force_authenticate(user=self.user)

    def test_create_ad_endpoint(self):
        """Test ad creation with step 1 data"""
        step1_data = {
            'category_id': self.category.id,
            'subcategory_id': self.subcategory.id,
            'specific_material': 'High-quality PP pellets',
            'packaging': 'octabin',
            'material_frequency': 'quarterly'
        }
        
        response = self.client.post('/api/ads/step/1/', step1_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['current_step'], 2)
        self.assertTrue(response.data['step_completion_status'][1])

    def test_step1_update(self):
        """Test step 1 creation (this is now the creation step)"""
        step1_data = {
            'category_id': self.category.id,
            'subcategory_id': self.subcategory.id,
            'packaging': 'octabin',
            'material_frequency': 'quarterly',
            'specific_material': 'High-quality PP pellets'
        }
        
        response = self.client.post('/api/ads/step/1/', step1_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['step'], 1)
        self.assertTrue(response.data['step_completion_status'][1])
        return response.data['data']['id']  # Return material ID for other tests

    def test_step3_update(self):
        """Test step 3 update (Material Origin)"""
        # Create ad with step 1 first
        material_id = self.test_step1_update()
        
        step3_data = {
            'origin': 'post_industrial'
        }
        
        response = self.client.put(f'/api/ads/{material_id}/step/3/', step3_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['origin'], 'post_industrial')

    def test_step7_pricing_update(self):
        """Test step 7 update (Quantity & Pricing)"""
        # Create ad with step 1 first
        material_id = self.test_step1_update()
        
        step7_data = {
            'available_quantity': 100,
            'unit_of_measurement': 'tons',
            'minimum_order_quantity': 5,
            'starting_bid_price': 29.50,
            'currency': 'EUR',
            'auction_duration': 7,
            'reserve_price': 35.00
        }
        
        response = self.client.put(f'/api/ads/{material_id}/step/7/', step7_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['data']['total_starting_value']), 2950.00)

    def test_step8_completion(self):
        """Test step 8 update (Title & Description) - completes the ad"""
        # Create ad with step 1 first
        material_id = self.test_step1_update()
        
        step8_data = {
            'title': 'High-Quality PP Industrial Pellets - Food Grade',
            'description': 'Premium polypropylene pellets suitable for food packaging applications. Clean, post-industrial material with excellent properties for injection molding and extrusion processes.',
            'keywords': 'PP, polypropylene, food grade, industrial, pellets'
        }
        
        response = self.client.put(f'/api/ads/{material_id}/step/8/', step8_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_complete'])
        self.assertIn('completed successfully', response.data['message'])

    def test_validation_endpoint(self):
        """Test step validation endpoint"""
        step1_data = {
            'category_id': self.category.id,
            'subcategory_id': self.subcategory.id,
            'packaging': 'octabin',
            'material_frequency': 'quarterly'
        }
        
        response = self.client.post('/api/ads/validate/step/1/', step1_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])

    def test_invalid_step_data(self):
        """Test validation with invalid data"""
        invalid_data = {
            'category_id': 999,  # Non-existent category
            'subcategory_id': 999
        }
        
        response = self.client.post('/api/ads/validate/step/1/', invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])

    def test_get_step_data(self):
        """Test retrieving step data"""
        # Create ad with step 1 first
        material_id = self.test_step1_update()
        
        # Get step 1 data
        response = self.client.get(f'/api/ads/{material_id}/step/1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['step'], 1)

    def test_list_user_ads(self):
        """Test listing user's ads"""
        # Create a few ads with step 1
        self.test_step1_update()
        self.test_step1_update()
        
        response = self.client.get('/api/ads/user/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        self.client.logout()
        response = self.client.post('/api/ads/step/1/', {
            'category_id': self.category.id,
            'subcategory_id': self.subcategory.id,
            'packaging': 'octabin',
            'material_frequency': 'quarterly'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com", 
            password="testpass123"
        )
        self.category = Category.objects.create(name="Plastics")
        self.subcategory = SubCategory.objects.create(
            name="PP",
            category=self.category
        )

    def test_step1_serializer_validation(self):
        """Test step 1 serializer validation"""
        ad = Ad.objects.create(user=self.user)
        
        valid_data = {
            'category_id': self.category.id,
            'subcategory_id': self.subcategory.id,
            'packaging': 'octabin',
            'material_frequency': 'quarterly'
        }
        
        serializer = AdStep1Serializer(ad, data=valid_data, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_step8_serializer_validation(self):
        """Test step 8 serializer validation with new rules (title >=3, description optional)"""
        ad = Ad.objects.create(user=self.user)

        # Valid: title >=3, no description
        valid_data = {
            'title': 'Mat'
        }
        serializer = AdStep8Serializer(ad, data=valid_data, partial=True)
        self.assertTrue(serializer.is_valid())

        # Invalid: title too short
        invalid_data = {
            'title': 'Hi'
        }
        serializer = AdStep8Serializer(ad, data=invalid_data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        # Description should not be required
        self.assertNotIn('description', serializer.errors)
