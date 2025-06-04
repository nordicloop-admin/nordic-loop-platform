from django.db import models
from category.models import Category,SubCategory, CategorySpecification
from company.models import Company
from users.models import User


class Ad(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('lb', 'Pound'),
        ('ton', 'Ton')
    ]

    SELLING_TYPE_CHOICES = [
        ('partition', 'Selling in Partition'),
        ('whole', 'Selling as Whole'),
        ('both whole and partion', 'selling as whole and partion'),
    ]

    MATERIAL_FREQUENCY_CHOICES = [
        ("one_time", "One Time"),
        ("weekly", "Weekly"),
        ("bi_weekly", "Bi-weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    MATERIAL_ORIGIN =[
        ('Post-industrial', 'Post-industrial'),
        ('Post-consumer', 'Post-consumer'),
        ('Mix', 'Mix')
    ]

    MATERIAL_CONTAMINATION =[
        ('Clean', 'Clean'),
        ('Slightly contaminated', 'Slightly contaminated'),
        ('Heavily contaminated', 'Heavily contaminated')
    ]

    ADDITIVES_CHOICE = [
        ('UV Stabilizer', 'UV Stabilizer'),
        ('Antioxidant', 'Antioxidant'),
        ('Flame retardants', 'Flame retardants'),
        ('Chlorides', 'Chlorides'),
        ('NO additives', 'No additives')
    ]

    STORAGE_CONDITION = [
        ('Climate Controlled', 'Climate Controlleld'),
        ('Protected Outdoor', 'Protected Outdoor'),
        ('Unprotected Outdoor', 'Uprotected Outdoor')
    ]



    PROCCESSING_CHOICES = [
        ('Blow moulding', 'Blow moulding'),
        ('Injection moulding', 'Injection moulding'),
        ('Extruion', 'Extrusion'),
        ('Calendering', 'Calenderng'),
        ('Rotational moulding', 'Rotation moulding'),
        ('Sintering', 'Sintering'),
        ('Thermoforming', 'Thermoforming')
    ]

    DELIVERY_OPTIONS =[
        ('Pickup only', 'Pickup only'),
        ('Local Delivery', 'Local DElivery'),
        ('National shipping', 'National Shipping'),
        ('International Shipping', 'International Shipping'),
        ('Freight Forwarding', 'Freight Forwarding')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ads", blank=True, null=True)
    item_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    material_frequency = models.CharField(max_length=20, choices=MATERIAL_FREQUENCY_CHOICES, null=True, blank=True)

    # step two 
    specification = models.OneToOneField(CategorySpecification, on_delete=models.SET_NULL, null=True, blank=True)

    # step three
    origin = models.CharField(max_length=20, choices=MATERIAL_ORIGIN, null=True, blank=True)

    # step four 
    contamination = models.CharField(max_length=255, choices=MATERIAL_CONTAMINATION,null=True, blank=True)
    additives = models.CharField(max_length= 255, choices=ADDITIVES_CHOICE, null=True, blank=True)
    storage = models.CharField(max_length= 255, choices=STORAGE_CONDITION, null=True, blank=True)

    # step five 
    processing_methods = models.CharField(max_length=255, choices=PROCCESSING_CHOICES, null=True, blank=True)

    # step 6 
    location = models.CharField(max_length=255, null=True, blank=True)
    delivery = models.CharField(max_length=255, choices=DELIVERY_OPTIONS, null=True, blank=True)

    # step 7
    




    
    # description = models.TextField(blank=True, null=True)
    # base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # price_per_partition = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # volume = models.DecimalField(max_digits=10, decimal_places=2)
    # unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    # selling_type = models.CharField(
    #     max_length=255,
    #     choices=SELLING_TYPE_CHOICES,
    #     default='whole',
    #     null=True
    # )
    # country_of_origin = models.CharField(max_length=255)
    # end_date = models.DateField()
    # end_time = models.TimeField()
    # item_image = models.ImageField(upload_to='auction_images/', null=True, blank=True)

    # def __str__(self):
    #     return self.item_name