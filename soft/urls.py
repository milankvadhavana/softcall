from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    AdminListCreateView, AdminDetailView, AdminStatusView, AllUsersView,
    AdminDashboardView,
    UserListCreateView, UserDetailView, UserStatusView,
    # ── Contact Views ──────────────────────────────────
    AdminContactListCreateView,
    AdminContactDetailView,
    AdminBulkUploadView,
    AdminContactDownloadTemplateView,
    UserContactListView,
    UserContactDetailView,
)

urlpatterns = [
    # Auth
    path('auth/login/',                        LoginView.as_view(),           name='login'),
    path('auth/token/refresh/',                TokenRefreshView.as_view(),    name='token-refresh'),

    # Superadmin → Admin Management
    path('superadmin/admins/',                 AdminListCreateView.as_view(),    name='admin-list-create'),
    path('superadmin/admins/<int:pk>/',        AdminDetailView.as_view(),        name='admin-detail'),
    path('superadmin/admins/<int:pk>/status/', AdminStatusView.as_view(),        name='admin-status'),
    path('superadmin/users/',                  AllUsersView.as_view(),           name='all-users'),

    # Admin Dashboard (only his own data)
    path('admin/dashboard/',                   AdminDashboardView.as_view(),  name='admin-dashboard'),

    # Admin → User Management
    path('admin/users/',                       UserListCreateView.as_view(),  name='user-list-create'),
    path('admin/users/<int:pk>/',              UserDetailView.as_view(),      name='user-detail'),
    path('admin/users/<int:pk>/status/',       UserStatusView.as_view(),      name='user-status'),
    # Admin → Contacts
    path('admin/contacts/',                     AdminContactListCreateView.as_view(),     name='admin-contact-list'),
    path('admin/contacts/upload/',              AdminBulkUploadView.as_view(),            name='admin-contact-upload'),
    path('admin/contacts/template/',            AdminContactDownloadTemplateView.as_view(),name='admin-contact-template'),
    path('admin/contacts/<int:pk>/',            AdminContactDetailView.as_view(),         name='admin-contact-detail'),
    
    # User → View their contacts only
    path('user/contacts/',                      UserContactListView.as_view(),            name='user-contacts'),
    path('user/contacts/<int:pk>/',             UserContactDetailView.as_view(), name='user-contact-detail'), 
]