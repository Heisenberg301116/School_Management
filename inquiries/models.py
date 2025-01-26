from django.db import models
from django.contrib.auth.models import User
from cities_light.models import City
    
class Agent(models.Model):   
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    performance_score = models.IntegerField(default=100)

    def __str__(self):
        return f"Name: {self.name},\nEmail: {self.email}"
    
    
class Lead(models.Model):
    STUDENT_CHOICES = [
        ('Nursery', 'Nursery'),
        ('LKG', 'LKG'),
        ('UKG', 'UKG'),
        ('Grade 1', 'Grade 1'),
        ('Grade 2', 'Grade 2'),
        ('Grade 3', 'Grade 3'),
        ('Grade 4', 'Grade 4'),
        ('Grade 5', 'Grade 5'),
        ('Grade 6', 'Grade 6'),
        ('Grade 7', 'Grade 7'),
        ('Grade 8', 'Grade 8'),
        ('Grade 9', 'Grade 9'),
        ('Grade 10', 'Grade 10'),
        ('Grade 11', 'Grade 11'),
        ('Grade 12', 'Grade 12'),
    ]

    INQUIRY_CHOICES = [
        ('Advertisement', 'Advertisement'),
        ('Walk-in', 'Walk-in'),
        ('Online Form', 'Online Form'),  
        ('Referral', 'Referral'),
    ]

    STATUS_CHOICES = [
        ('Inquiry', 'Inquiry'),
        ('Registration', 'Registration'),
        ('Admission Test', 'Admission Test'),
        ('Admission Offered', 'Admission Offered'),
        ('Admission Confirmed', 'Admission Confirmed'),
        ('Rejected', 'Rejected'),
    ]

    student_name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=100, unique=True)
    address = models.TextField()    
    location_tag = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    inquiry_source = models.CharField(choices = INQUIRY_CHOICES, max_length=100)  # e.g., Advertisement, Walk-in, Online
    student_class = models.CharField(choices=STUDENT_CHOICES, max_length=10)
    status = models.CharField(choices=STATUS_CHOICES, max_length=100, default='Inquiry')  # Inquiry, Follow-up, Visit, etc.    
    remarks = models.TextField(blank=True, null=True)
    inquiry_date = models.DateField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    admission_test_date = models.DateField(null=True, blank=True)
    admission_offered_date = models.DateField(null=True, blank=True)
    admission_confirmed_date = models.DateField(null=True, blank=True)
    rejected_date = models.DateField(null=True, blank=True)
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    admin_assigned = models.ForeignKey(
        User,  # Refers to Django's built-in User model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_staff': True}  # Restrict to staff users (admins)
    )
    

    def __str__(self):
        return f"Name: {self.student_name},\nParent Name: {self.parent_name},Email:{self.email},Student Class:{self.student_class},\nmobile_number:{self.mobile_number},\nAddress:{self.address},\nLocation Tag:{self.location_tag},\nInquiry Source:{self.inquiry_source},\nStatus:{self.status}"