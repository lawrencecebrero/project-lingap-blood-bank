from django import forms
from .models import Donor, BloodInventory, BloodRequest, Campaign
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ObjectDoesNotExist

class DonorForm(forms.ModelForm):
    blood_type = forms.ChoiceField(
        choices=[('', "I don't know my blood type")] + list(Donor.BLOOD_TYPES),
        required=False,
        label="Blood Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Donor
        fields = ['first_name', 'last_name', 'email', 'blood_type', 'contact_no', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XX-XXX-XXXX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        donor = super().save(commit=False)

        try:
            if donor.user:
                donor.user.first_name = self.cleaned_data.get('first_name')
                donor.user.last_name = self.cleaned_data.get('last_name')
                donor.user.email = self.cleaned_data.get('email')

                if commit:
                    donor.user.save()  # Update User table
                    donor.save()  # Update Donor table

        except ObjectDoesNotExist:
            if commit:
                donor.save()

        return donor

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['title', 'location', 'start_datetime', 'end_datetime', 'description']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = [
            'patient_name', 'patient_blood_type', 'hospital_name',
            'hospital_address', 'physician_name', 'physician_license',
            'component', 'quantity', 'urgency', 'reason'
        ]
        widgets = {
            'hospital_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class InventoryDonationForm(forms.ModelForm):
    class Meta:
        model = BloodInventory
        fields = ['serial_number', 'blood_group', 'donor', 'expiry_date', 'status']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'donor': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['donor'].required = False
        self.fields['donor'].label = "Source / Donor (Optional)"
        self.fields['donor'].empty_label = "--- External Source / Anonymous ---"
        self.fields['blood_group'].required = True

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }


class AdminDonorCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=100,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    blood_type = forms.ChoiceField(choices=Donor.BLOOD_TYPES, widget=forms.Select(attrs={'class': 'form-select'}))
    contact_no = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()

            Donor.objects.create(
                user=user,
                blood_type=self.cleaned_data['blood_type'],
                contact_no=self.cleaned_data['contact_no'],
                address=self.cleaned_data['address']
            )
        return user


class RequestDispositionForm(forms.ModelForm):
    blood_bag = forms.ModelChoiceField(
        queryset=BloodInventory.objects.none(),
        required=False,
        label="Assign Blood Unit (Required for Approval)",
        empty_label="--- Select a Matching Blood Bag ---",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = BloodRequest
        fields = ['status', 'assigned_bag']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            available_bags = BloodInventory.objects.filter(
                status='AVAILABLE',
                blood_group=self.instance.patient_blood_type
            )

            if self.instance.assigned_bag:
                current_bag = BloodInventory.objects.filter(pk=self.instance.assigned_bag.pk)
                self.fields['blood_bag'].queryset = available_bags | current_bag
                self.fields['blood_bag'].initial = self.instance.assigned_bag
            else:
                self.fields['blood_bag'].queryset = available_bags

class VolunteerCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Grants "Red Cross" access
        if commit:
            user.save()
        return user

class VolunteerUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class CampaignDonationForm(forms.ModelForm):
    class Meta:
        model = BloodInventory
        fields = ['serial_number', 'expiry_date']
        widgets = {
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Serial No.'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }