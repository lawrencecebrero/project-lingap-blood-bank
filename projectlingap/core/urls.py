from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # PUBLIC LANDING PAGE
    path('', views.landing_page, name='home'),

    # AUTHENTICATION
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),  # Redirect to home after logout
    path('register/', views.register_view, name='register'),

    # DASHBOARD REDIRECT
    path('dashboard/', views.dashboard_view, name='dashboard'),  # <--- New path for smart redirect

    # RED CROSS / ADMIN ROUTES
    path('redcross/dashboard/', views.redcross_dashboard, name='redcross_dashboard'),
    path('campaign/create/', views.CampaignCreateView.as_view(), name='campaign_create'),
    path('campaign/manage/<int:pk>/', views.campaign_manage, name='campaign_manage'),
    path('campaign/record-donation/<int:campaign_id>/<int:donor_id>/', views.record_donation, name='record_donation'),
    path('donors/', views.DonorListView.as_view(), name='donor_list'),
    path('donors/add/', views.AdminDonorCreateView.as_view(), name='donor_create'),
    path('donors/edit/<int:pk>/', views.DonorUpdateView.as_view(), name='donor_update'),
    path('campaign/manage/<int:pk>/', views.campaign_manage, name='campaign_manage'),
    path('campaign/edit/<int:pk>/', views.CampaignUpdateView.as_view(), name='campaign_edit'),
    path('campaign/delete/<int:pk>/', views.CampaignDeleteView.as_view(), name='campaign_delete'),
    path('dashboard/admin/', views.superuser_dashboard, name='superuser_dashboard'),
    path('volunteers/', views.VolunteerListView.as_view(), name='volunteer_list'),
    path('volunteers/add/', views.VolunteerCreateView.as_view(), name='volunteer_add'),
    path('volunteers/<int:pk>/edit/', views.VolunteerUpdateView.as_view(), name='volunteer_edit'),
    path('volunteers/<int:pk>/delete/', views.VolunteerDeleteView.as_view(), name='volunteer_delete'),

    # DONOR ROUTES
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('donor/create-profile/', views.create_donor_profile, name='create_donor_profile'),
    path('campaigns/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/join/<int:pk>/', views.join_campaign, name='join_campaign'),
    path('donor/history/', views.donor_history_view, name='donor_history'),

    # BLOOD REQUESTS
    path('request/blood/', views.RequestCreateView.as_view(), name='request_blood'),
    path('requests/', views.RequestListView.as_view(), name='request_list'),
    path('requests/manage/<int:pk>/', views.RequestUpdateView.as_view(), name='request_manage'),

    # INVENTORY & DONOR MANAGEMENT
    path('inventory/', views.InventoryListView.as_view(), name='inventory_list'),
    path('inventory/add/', views.InventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/edit/<int:pk>/', views.InventoryUpdateView.as_view(), name='inventory_update'),
    path('inventory/delete/<int:pk>/', views.InventoryDeleteView.as_view(), name='inventory_delete'),

    path('donors/', views.DonorListView.as_view(), name='donor_list'),
    path('donors/edit/<int:pk>/', views.DonorUpdateView.as_view(), name='donor_update'),
    path('donors/delete/<int:pk>/', views.DonorDeleteView.as_view(), name='donor_delete'),

    # SETTINGS
    path('profile/', views.profile_view, name='profile'),
]