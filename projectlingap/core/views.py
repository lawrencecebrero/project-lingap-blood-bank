from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.utils.decorators import method_decorator
from .forms import CampaignDonationForm
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from .models import (
    Donor,
    BloodInventory,
    BloodRequest,
    Campaign,
    CampaignParticipant
)
from .forms import (
    UserRegistrationForm,
    DonorForm,
    BloodRequestForm,
    CampaignForm,
    InventoryDonationForm,
    UserUpdateForm,
    AdminDonorCreationForm,
    RequestDispositionForm,
    VolunteerCreationForm,
    VolunteerUpdateForm
)

# PUBLIC LANDING PAGE
def landing_page(request):
    return render(request, 'core/home.html')

# DASHBOARD REDIRECTOR
@login_required
def dashboard_view(request):
    if is_red_cross(request.user):
        return redirect('redcross_dashboard')
    else:
        return redirect('donor_dashboard')

def is_red_cross(user):
    return user.is_staff or user.groups.filter(name='Red Cross').exists()


def is_donor(user):
    return not user.is_staff

# MAIN DASHBOARD
@login_required
def dashboard_view(request):
    if is_red_cross(request.user):
        return redirect('redcross_dashboard')
    else:
        return redirect('donor_dashboard')


# RED CROSS / ADMIN SIDE
@login_required
@user_passes_test(is_red_cross)
def redcross_dashboard(request):

    pending_requests = BloodRequest.objects.filter(status='PENDING').count()
    available_blood = BloodInventory.objects.filter(status='AVAILABLE').count()
    active_campaigns = Campaign.objects.filter(end_datetime__gt=timezone.now()).count()

    recent_donations = BloodInventory.objects.all().order_by('-date_collected')[:5]

    context = {
        'pending_requests': pending_requests,
        'available_blood': available_blood,
        'active_campaigns': active_campaigns,
        'recent_donations': recent_donations,
    }
    return render(request, 'core/dashboard_redcross.html', context)


class CampaignCreateView(CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'core/campaign_form.html'
    success_url = reverse_lazy('redcross_dashboard')

    @method_decorator(user_passes_test(is_red_cross))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


@login_required
@user_passes_test(is_red_cross)
def campaign_manage(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    participants = campaign.participants.select_related('donor', 'donor__user').all()

    total_participants = participants.count()
    donated_count = participants.filter(has_donated=True).count()

    context = {
        'campaign': campaign,
        'participants': participants,
        'total_participants': total_participants,
        'donated_count': donated_count,  # Pass this clear number to the template
    }
    return render(request, 'core/campaign_manage.html', context)


@login_required
@user_passes_test(is_red_cross)
def record_donation(request, campaign_id, donor_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    donor = get_object_or_404(Donor, pk=donor_id)

    if request.method == 'POST':
        form = CampaignDonationForm(request.POST)

        if form.is_valid():
            inventory = form.save(commit=False)

            inventory.donor = donor
            inventory.campaign = campaign
            inventory.blood_group = donor.blood_type
            inventory.status = 'AVAILABLE'
            inventory.processed_by = request.user

            inventory.save()

            participant = CampaignParticipant.objects.filter(campaign=campaign, donor=donor).first()
            if participant:
                participant.has_donated = True
                participant.save()

            messages.success(request, f"Donation recorded for {donor.user.get_full_name()}")
            return redirect('campaign_manage', pk=campaign.id)
        else:
            print("Form Errors:", form.errors)
    else:
        form = CampaignDonationForm()

    return render(request, 'core/record_donation.html', {'form': form, 'donor': donor, 'campaign': campaign})

# DONOR SIDE
@login_required
def donor_dashboard(request):
    try:
        donor = request.user.donor_profile
    except Donor.DoesNotExist:
        return redirect('create_donor_profile')

    donation_count = BloodInventory.objects.filter(donor=donor).count()

    donations = BloodInventory.objects.filter(donor=donor).order_by('-date_collected')[:5]
    requests = BloodRequest.objects.filter(processed_by=request.user).order_by('-request_date')[:5]

    user_requests = BloodRequest.objects.filter(requestor=request.user).order_by('-request_date')[:5]

    context = {
        'donor': donor,
        'donation_count': donation_count,
        'donations': donations,
        'requests': user_requests,  # Using the sliced lists
    }
    return render(request, 'core/dashboard_donor.html', context)


# CREATE NEW HISTORY VIEW
@login_required
def donor_history_view(request):
    try:
        donor = request.user.donor_profile
    except Donor.DoesNotExist:
        return redirect('create_donor_profile')

    donation_list = BloodInventory.objects.filter(donor=donor).order_by('-date_collected')
    request_list = BloodRequest.objects.filter(requestor=request.user).order_by('-request_date')

    p_donations = Paginator(donation_list, 5)
    d_page_num = request.GET.get('d_page')
    page_donations = p_donations.get_page(d_page_num)

    p_requests = Paginator(request_list, 5)
    r_page_num = request.GET.get('r_page')
    page_requests = p_requests.get_page(r_page_num)

    context = {
        'page_donations': page_donations,
        'page_requests': page_requests,
    }
    return render(request, 'core/history.html', context)

class CampaignListView(LoginRequiredMixin, ListView):
    model = Campaign
    template_name = 'core/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 6

    def get_queryset(self):
        if is_red_cross(self.request.user):
            return Campaign.objects.all().order_by('-start_datetime')
        else:
            return Campaign.objects.filter(start_datetime__gte=timezone.now()).order_by('start_datetime')


@login_required
def join_campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    donor = request.user.donor_profile

    obj, created = CampaignParticipant.objects.get_or_create(campaign=campaign, donor=donor)

    if created:
        messages.success(request, f"You have joined {campaign.title}!")
    else:
        messages.info(request, "You are already registered for this campaign.")

    return redirect('donor_dashboard')


# REQUESTS (SHARED)

class RequestCreateView(LoginRequiredMixin, CreateView):
    model = BloodRequest
    form_class = BloodRequestForm
    template_name = 'core/request_form.html'
    success_url = reverse_lazy('donor_dashboard')

    def form_valid(self, form):
        form.instance.requestor = self.request.user
        messages.success(self.request, "Blood request submitted successfully.")
        return super().form_valid(form)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Please complete your profile.")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


@login_required
def create_donor_profile(request):
    if request.method == 'POST':
        form = DonorForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()

            return redirect('donor_dashboard')
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        }
        form = DonorForm(initial=initial_data)

    return render(request, 'core/donor_profile_create.html', {'form': form})

# MISSING INVENTORY VIEWS

# UPDATED INVENTORY LIST VIEW
class InventoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BloodInventory
    template_name = 'core/inventory_list.html'
    context_object_name = 'inventory_items'
    ordering = ['expiry_date']
    paginate_by = 8  # LIMIT TO 8 PER PAGE

    def test_func(self):
        return is_red_cross(self.request.user)

    def get_queryset(self):
        queryset = BloodInventory.objects.all().order_by('expiry_date')

        search_query = self.request.GET.get('q')
        blood_filter = self.request.GET.get('blood_group')
        status_filter = self.request.GET.get('status')

        if search_query:
            queryset = queryset.filter(serial_number__icontains=search_query)

        if blood_filter:
            queryset = queryset.filter(blood_group=blood_filter)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['search_params'] = query_params.urlencode()
        return context

class InventoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = BloodInventory
    form_class = InventoryDonationForm  # Or InventoryForm if you kept the original
    template_name = 'core/inventory_form.html'
    success_url = reverse_lazy('inventory_list')

    def test_func(self):
        return is_red_cross(self.request.user)

    def form_valid(self, form):
        form.instance.processed_by = self.request.user
        return super().form_valid(form)

class InventoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BloodInventory
    form_class = InventoryDonationForm
    template_name = 'core/inventory_form.html'
    success_url = reverse_lazy('inventory_list')

    def test_func(self):
        return is_red_cross(self.request.user)

class InventoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = BloodInventory
    template_name = 'core/inventory_confirm_delete.html'
    success_url = reverse_lazy('inventory_list')

    def test_func(self):
        return is_red_cross(self.request.user)

# UPDATED DONOR LIST VIEW
class DonorListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Donor
    template_name = 'core/donor_list.html'
    context_object_name = 'donors'
    ordering = ['-user__date_joined']
    paginate_by = 8  # LIMIT TO 8 PER PAGE

    def test_func(self):
        return is_red_cross(self.request.user)

    def get_queryset(self):
        queryset = Donor.objects.all().select_related('user').order_by('-id')

        search_query = self.request.GET.get('q')
        blood_filter = self.request.GET.get('blood_type')

        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )

        if blood_filter:
            queryset = queryset.filter(blood_type=blood_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['search_params'] = query_params.urlencode()
        return context

class DonorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Donor
    form_class = DonorForm
    template_name = 'core/donor_form.html'
    success_url = reverse_lazy('donor_list')

    def test_func(self):
        return is_red_cross(self.request.user)

class DonorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Donor
    template_name = 'core/donor_confirm_delete.html'
    success_url = reverse_lazy('donor_list')

    def test_func(self):
        return is_red_cross(self.request.user)


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'core/profile.html', {'form': form})


class AdminDonorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = AdminDonorCreationForm
    template_name = 'core/donor_form_admin.html'
    success_url = reverse_lazy('donor_list')

    def test_func(self):
        return is_red_cross(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "New donor account created successfully!")
        return super().form_valid(form)


class CampaignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'core/campaign_form.html'

    def test_func(self):
        return is_red_cross(self.request.user)

    def get_success_url(self):
        return reverse_lazy('campaign_manage', kwargs={'pk': self.object.pk})

class CampaignDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Campaign
    template_name = 'core/campaign_confirm_delete.html'
    success_url = reverse_lazy('campaign_list')

    def test_func(self):
        return is_red_cross(self.request.user)

# BLOOD REQUEST MANAGEMENT

class RequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BloodRequest
    template_name = 'core/request_list.html'
    context_object_name = 'requests'
    ordering = ['-request_date']
    paginate_by = 8  # <--- LIMIT TO 8 PER PAGE

    def test_func(self):
        return is_red_cross(self.request.user)

    def get_queryset(self):
        queryset = BloodRequest.objects.all().order_by('-request_date')

        search_query = self.request.GET.get('q')  # The search box
        status_filter = self.request.GET.get('status')  # The dropdown
        urgency_filter = self.request.GET.get('urgency')
        blood_filter = self.request.GET.get('blood_type')

        if search_query:
            queryset = queryset.filter(
                Q(patient_name__icontains=search_query) |
                Q(hospital_name__icontains=search_query) |
                Q(physician_name__icontains=search_query)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if urgency_filter:
            queryset = queryset.filter(urgency=urgency_filter)

        if blood_filter:
            queryset = queryset.filter(patient_blood_type=blood_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['search_params'] = query_params.urlencode()
        return context


class RequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BloodRequest
    form_class = RequestDispositionForm  # <--- USE THE NEW FORM
    template_name = 'core/request_manage.html'
    success_url = reverse_lazy('request_list')

    def test_func(self):
        return is_red_cross(self.request.user)

    def form_valid(self, form):
        new_status = form.cleaned_data['status']
        selected_bag = form.cleaned_data['blood_bag']
        request_obj = form.instance

        if new_status == 'APPROVED':
            if not selected_bag:
                form.add_error('blood_bag', 'You must select a blood bag to approve this request.')
                return self.form_invalid(form)

            selected_bag.status = 'RESERVED'
            selected_bag.save()
            request_obj.assigned_bag = selected_bag

        elif new_status == 'COMPLETED':
            bag_to_distribute = selected_bag or request_obj.assigned_bag

            if bag_to_distribute:
                bag_to_distribute.status = 'DISTRIBUTED'
                bag_to_distribute.save()
                request_obj.assigned_bag = bag_to_distribute
            else:
                form.add_error('blood_bag', 'No blood bag assigned. Please select one to complete distribution.')
                return self.form_invalid(form)

        elif new_status in ['PENDING', 'REJECTED']:
            if request_obj.assigned_bag:
                old_bag = request_obj.assigned_bag
                old_bag.status = 'AVAILABLE'
                old_bag.save()
                request_obj.assigned_bag = None

        messages.success(self.request, f"Request updated to {new_status}")
        return super().form_valid(form)

@login_required
@user_passes_test(lambda u: u.is_superuser)  # Only Superusers can access
def superuser_dashboard(request):
    pending_requests = BloodRequest.objects.filter(status='PENDING').count()
    available_blood = BloodInventory.objects.filter(status='AVAILABLE').count()
    active_campaigns = Campaign.objects.filter(end_datetime__gt=timezone.now()).count()

    total_donors = Donor.objects.count()
    total_volunteers = User.objects.filter(is_staff=True, is_superuser=False).count()

    context = {
        'pending_requests': pending_requests,
        'available_blood': available_blood,
        'active_campaigns': active_campaigns,
        'total_donors': total_donors,
        'total_volunteers': total_volunteers,
    }
    return render(request, 'core/dashboard_superuser.html', context)

@login_required
def dashboard_view(request):
    if request.user.is_superuser:
        return redirect('superuser_dashboard')

    elif request.user.is_staff or request.user.groups.filter(name='Red Cross').exists():
        return redirect('redcross_dashboard')

    else:
        return redirect('donor_dashboard')

class VolunteerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'core/volunteer_list.html'
    context_object_name = 'volunteers'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return User.objects.filter(is_staff=True, is_superuser=False).order_by('-date_joined')

class VolunteerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = VolunteerCreationForm
    template_name = 'core/volunteer_form.html'
    success_url = reverse_lazy('volunteer_list')

    def test_func(self):
        return self.request.user.is_superuser  # Only Admin can add staff

    def form_valid(self, form):
        messages.success(self.request, "New volunteer account created successfully.")
        return super().form_valid(form)

class VolunteerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = VolunteerUpdateForm
    template_name = 'core/volunteer_form.html'
    success_url = reverse_lazy('volunteer_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, "Volunteer details updated.")
        return super().form_valid(form)

class VolunteerDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'core/volunteer_confirm_delete.html'
    success_url = reverse_lazy('volunteer_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.warning(self.request, "Volunteer account has been removed.")
        return super().form_valid(form)

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('dashboard')

class DonorProfileCreateView(LoginRequiredMixin, CreateView):
    model = Donor
    form_class = DonorForm
    template_name = 'core/donor_profile_create.html'
    success_url = reverse_lazy('donor_dashboard')

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        initial['email'] = user.email
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)