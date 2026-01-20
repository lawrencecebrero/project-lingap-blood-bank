from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    BLOOD_TYPES = [
        ('A+', 'A Positive'), ('A-', 'A Negative'),
        ('B+', 'B Positive'), ('B-', 'B Negative'),
        ('AB+', 'AB Positive'), ('AB-', 'AB Negative'),
        ('O+', 'O Positive'), ('O-', 'O Negative'),
    ]
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, null=True, blank=True)
    contact_no = models.CharField(max_length=15)
    address = models.TextField()

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=254, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.blood_type})"

class Campaign(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.start_datetime.date()}"

    @property
    def is_active(self):
        return self.end_datetime >= timezone.now()

class CampaignParticipant(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='participants')
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    has_donated = models.BooleanField(default=False)

    class Meta:
        unique_together = ('campaign', 'donor')

class BloodInventory(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('RESERVED', 'Reserved'),
        ('EXPIRED', 'Expired'),
        ('DISTRIBUTED', 'Distributed'),
    ]

    serial_number = models.CharField(max_length=50, unique=True)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations', null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=Donor.BLOOD_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    date_collected = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.blood_group and self.donor:
            self.blood_group = self.donor.blood_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.serial_number} ({self.blood_group})"

class BloodRequest(models.Model):
    URGENCY_LEVELS = [('ROUTINE', 'Routine'), ('URGENT', 'Urgent'), ('CRITICAL', 'Critical')]
    STATUS_CHOICES = [('PENDING', 'Pending Validation'), ('APPROVED', 'Approved'), ('COMPLETED', 'Completed'),
                      ('REJECTED', 'Rejected')]
    COMPONENT_CHOICES = [('WHOLE', 'Whole Blood'), ('PLASMA', 'Plasma'), ('PLATELETS', 'Platelets')]

    requestor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    assigned_bag = models.OneToOneField('BloodInventory', on_delete=models.SET_NULL, null=True, blank=True, related_name='request_assignment')

    patient_name = models.CharField(max_length=150)
    patient_blood_type = models.CharField(max_length=3, choices=Donor.BLOOD_TYPES)
    hospital_name = models.CharField(max_length=200)
    hospital_address = models.TextField()
    physician_name = models.CharField(max_length=150)
    physician_license = models.CharField(max_length=50)

    component = models.CharField(max_length=20, choices=COMPONENT_CHOICES, default='WHOLE')
    quantity = models.PositiveIntegerField(default=1)
    urgency = models.CharField(max_length=10, choices=URGENCY_LEVELS, default='ROUTINE')
    reason = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    request_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_requests',
                                     blank=True)

    def __str__(self):
        return f"{self.patient_name} ({self.urgency}) - {self.status}"