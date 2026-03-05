"""
soft/admin.py — COMPLETE FINAL with Advanced Filters
New: Date filter, Assigned To filter, Added By filter, full search
"""

import csv
import pandas as pd
from datetime import date, timedelta
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path
from django.template.response import TemplateResponse
from django.utils import timezone

from .models import CustomUser, ContactData


def assign_admin_permissions(user):
    if user.role != 'admin':
        return
    contact_ct = ContentType.objects.get_for_model(ContactData)
    user_ct    = ContentType.objects.get_for_model(CustomUser)
    perms      = Permission.objects.filter(content_type__in=[contact_ct, user_ct])
    user.user_permissions.set(perms)


BULK_BTN = (
    '<div style="margin:8px 0 12px 0;">'
    '<a href="/admin/soft/contactdata/bulk-upload/" '
    'style="background:#17a2b8;color:#fff;padding:8px 18px;'
    'border-radius:4px;text-decoration:none;font-weight:bold;font-size:13px;">'
    '📤 Bulk Upload Excel / CSV'
    '</a></div>'
)


def inject_btn(response):
    if isinstance(response, TemplateResponse):
        response.render()
    if hasattr(response, 'content'):
        try:
            html = response.content.decode('utf-8')
            marker = '<div id="content-main">'
            if marker in html:
                html = html.replace(marker, marker + BULK_BTN, 1)
                response.content = html.encode('utf-8')
        except Exception:
            pass
    return response


# ═══════════════════════════════════════════════════════
#  CUSTOM DATE FILTER
# ═══════════════════════════════════════════════════════

class CreatedDateFilter(admin.SimpleListFilter):
    title        = 'Date Added'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return [
            ('today',      '📅 Today'),
            ('yesterday',  '📅 Yesterday'),
            ('this_week',  '📅 This Week'),
            ('last_7',     '📅 Last 7 Days'),
            ('this_month', '📅 This Month'),
            ('last_30',    '📅 Last 30 Days'),
        ]

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'today':
            return queryset.filter(created_at__date=today)
        if self.value() == 'yesterday':
            return queryset.filter(created_at__date=today - timedelta(days=1))
        if self.value() == 'this_week':
            start = today - timedelta(days=today.weekday())
            return queryset.filter(created_at__date__gte=start)
        if self.value() == 'last_7':
            return queryset.filter(created_at__date__gte=today - timedelta(days=7))
        if self.value() == 'this_month':
            return queryset.filter(created_at__year=today.year, created_at__month=today.month)
        if self.value() == 'last_30':
            return queryset.filter(created_at__date__gte=today - timedelta(days=30))
        return queryset


# ═══════════════════════════════════════════════════════
#  CUSTOM ADDED BY FILTER (shows only relevant admins)
# ═══════════════════════════════════════════════════════

class AddedByFilter(admin.SimpleListFilter):
    title          = 'Added By'
    parameter_name = 'added_by'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            admins = CustomUser.objects.filter(
                role__in=['admin', 'superadmin']
            ).order_by('name')
        else:
            admins = CustomUser.objects.filter(pk=request.user.pk)
        return [(a.pk, f'{a.name} ({a.role})') for a in admins]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(added_by__pk=self.value())
        return queryset


# ═══════════════════════════════════════════════════════
#  CUSTOM ASSIGNED TO FILTER
# ═══════════════════════════════════════════════════════

class AssignedToFilter(admin.SimpleListFilter):
    title          = 'Assigned To'
    parameter_name = 'assigned_to'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            users = CustomUser.objects.filter(role='user').order_by('name')
        else:
            users = CustomUser.objects.filter(
                role='user', created_by=request.user
            ).order_by('name')
        return [(u.pk, u.name) for u in users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(assigned_to__pk=self.value())
        return queryset


# ═══════════════════════════════════════════════════════
#  SUPERADMIN — CustomUser panel
# ═══════════════════════════════════════════════════════

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):

    list_display    = ['id', 'name', 'email', 'mobile', 'role',
                       'colored_status', 'plan_badge', 'created_at']
    list_filter     = ['role', 'status']
    search_fields   = ['name', 'email', 'mobile', 'company']
    ordering        = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Personal Info',      {'fields': ('name', 'email', 'mobile', 'password')}),
        ('Role & Status',      {'fields': ('role', 'status')}),
        ('Admin Plan Details', {'fields': ('company', 'plan_start', 'plan_end')}),
        ('Hierarchy',          {'classes': ('collapse',), 'fields': ('created_by',)}),
        ('Permissions',        {'classes': ('collapse',), 'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps',         {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields':  ('name', 'email', 'mobile', 'password1', 'password2',
                        'role', 'status', 'company', 'plan_start', 'plan_end'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if getattr(request.user, 'role', None) == 'admin':
            return qs.filter(role='user', created_by=request.user)
        return qs.none()

    def has_add_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser: return True
        if getattr(request.user, 'role', None) == 'admin':
            return obj is None or obj.created_by == request.user
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser: return True
        if getattr(request.user, 'role', None) == 'admin':
            return obj is None or obj.created_by == request.user
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'

    def save_model(self, request, obj, form, change):
        if obj.role == 'admin':
            obj.is_staff = True
            obj.is_superuser = False
        elif obj.role == 'user':
            obj.is_staff = False
            obj.is_superuser = False
            if not change:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)
        if obj.role == 'admin':
            assign_admin_permissions(obj)

    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser and getattr(request.user, 'role', None) == 'admin':
            if obj is None:
                return (('Create New User', {'fields': ('name', 'email', 'mobile', 'password1', 'password2', 'status')}),)
            return (('Edit User', {'fields': ('name', 'email', 'mobile', 'password', 'status')}),)
        return super().get_fieldsets(request, obj)

    def colored_status(self, obj):
        colors = {'active': '#28a745', 'inactive': '#fd7e14', 'suspended': '#dc3545'}
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:12px;font-weight:bold;">{}</span>',
            colors.get(obj.status, '#6c757d'), obj.status.upper()
        )
    colored_status.short_description = 'Status'

    def plan_badge(self, obj):
        if obj.role != 'admin': return '—'
        if obj.is_plan_active:
            return format_html('<span style="color:#28a745;font-weight:bold;">✔ Active</span>')
        return format_html('<span style="color:#dc3545;font-weight:bold;">✘ Expired</span>')
    plan_badge.short_description = 'Plan'


# ═══════════════════════════════════════════════════════
#  BULK UPLOAD FORM
# ═══════════════════════════════════════════════════════

class BulkUploadForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset    = CustomUser.objects.none(),
        label       = "Assign all contacts to",
        empty_label = "— Select User —"
    )
    file = forms.FileField(label="Upload CSV or Excel file")


# ═══════════════════════════════════════════════════════
#  CONTACT DATA ADMIN  ← Main changes here
# ═══════════════════════════════════════════════════════

@admin.register(ContactData)
class ContactDataAdmin(admin.ModelAdmin):

    list_display    = ['id', 'name', 'contact_number', 'email',
                       'assigned_to', 'added_by', 'created_at']

    # ✅ Rich filter panel on right side
    list_filter     = [
        CreatedDateFilter,   # Today / Yesterday / This Week / Last 7 Days / This Month
        AssignedToFilter,    # Filter by which user contacts are assigned to
        AddedByFilter,       # Filter by which admin added them
    ]

    # ✅ Search across name, number, email, assigned user name, added by name
    search_fields   = [
        'name',
        'contact_number',
        'email',
        'assigned_to__name',
        'added_by__name',
    ]

    # ✅ Date hierarchy drill-down at top (Year → Month → Day)
    date_hierarchy  = 'created_at'

    ordering        = ['-created_at']
    actions         = ['export_as_csv']
    readonly_fields = ['added_by', 'created_at', 'updated_at']
    fields          = ['assigned_to', 'name', 'contact_number', 'email']

    # ✅ How many per page
    list_per_page   = 25

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                'bulk-upload/',
                self.admin_site.admin_view(self.bulk_upload_view),
                name='soft_contactdata_bulk_upload',
            ),
        ] + urls

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if getattr(request.user, 'role', None) == 'admin':
            return qs.filter(added_by=request.user)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'assigned_to':
            if not request.user.is_superuser and getattr(request.user, 'role', None) == 'admin':
                kwargs['queryset'] = CustomUser.objects.filter(
                    role='user', created_by=request.user, status='active'
                )
            else:
                kwargs['queryset'] = CustomUser.objects.filter(role='user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        return inject_btn(response)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        response = super().changeform_view(request, object_id, form_url, extra_context)
        return inject_btn(response)

    # ── Bulk upload ───────────────────────────────────────
    def bulk_upload_view(self, request):
        if request.user.is_superuser:
            own_users_qs = CustomUser.objects.filter(role='user', status='active')
        elif getattr(request.user, 'role', None) == 'admin':
            if not request.user.is_account_active:
                messages.error(request, "Your plan has expired.")
                return redirect('../')
            own_users_qs = CustomUser.objects.filter(
                role='user', created_by=request.user, status='active'
            )
        else:
            messages.error(request, "Access denied.")
            return redirect('../')

        form = BulkUploadForm()
        form.fields['assigned_to'].queryset = own_users_qs

        if request.method == 'POST':
            form = BulkUploadForm(request.POST, request.FILES)
            form.fields['assigned_to'].queryset = own_users_qs

            if form.is_valid():
                file        = request.FILES['file']
                target_user = form.cleaned_data['assigned_to']
                filename    = file.name.lower()

                try:
                    df = pd.read_csv(file) if filename.endswith('.csv') else pd.read_excel(file)
                except Exception as exc:
                    messages.error(request, f"Cannot read file: {exc}")
                    return render(request, 'admin/bulk_upload.html',
                                  {'form': form, 'title': 'Bulk Upload', 'opts': self.model._meta})

                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

                if 'name' not in df.columns or 'contact_number' not in df.columns:
                    messages.error(request, "File must have: name, contact_number (email optional)")
                    return render(request, 'admin/bulk_upload.html',
                                  {'form': form, 'title': 'Bulk Upload', 'opts': self.model._meta})

                contacts, skipped = [], 0
                for _, row in df.iterrows():
                    name  = str(row.get('name', '')).strip()
                    phone = str(row.get('contact_number', '')).strip()
                    email = str(row.get('email', '')).strip() if 'email' in df.columns else ''
                    if not name or name == 'nan' or not phone or phone == 'nan':
                        skipped += 1; continue
                    contacts.append(ContactData(
                        added_by=request.user, assigned_to=target_user,
                        name=name, contact_number=phone,
                        email=email if email and email != 'nan' else None,
                    ))

                ContactData.objects.bulk_create(contacts)
                messages.success(request,
                    f"✅ {len(contacts)} contacts saved for '{target_user.name}'. {skipped} skipped.")
                return redirect('/admin/soft/contactdata/')

        return render(request, 'admin/bulk_upload.html', {
            'form': form, 'title': 'Bulk Upload Contacts', 'opts': self.model._meta,
        })

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contacts.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Contact Number', 'Email', 'Assigned To', 'Added By', 'Created At'])
        for obj in queryset:
            writer.writerow([
                obj.name, obj.contact_number, obj.email or '',
                obj.assigned_to.name, obj.added_by.name,
                obj.created_at.strftime('%Y-%m-%d %H:%M'),
            ])
        return response
    export_as_csv.short_description = "📥 Export selected as CSV"