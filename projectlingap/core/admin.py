from django.contrib import admin
from .models import Donor, BloodInventory, BloodRequest, Campaign

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    # Use a custom method to get the name from the User model
    list_display = ('get_full_name', 'blood_type', 'contact_no')

    # Search the RELATED User table, not the Donor table
    search_fields = ('user__first_name', 'user__last_name', 'blood_type')
    list_filter = ('blood_type',)

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'Donor Name'

@admin.register(BloodInventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'blood_group', 'status', 'expiry_date', 'donor')
    search_fields = ('serial_number',)
    list_filter = ('status', 'blood_group', 'expiry_date')

@admin.register(BloodRequest)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'urgency', 'status', 'hospital_name')
    list_filter = ('status', 'urgency', 'component')

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'start_datetime', 'end_datetime')