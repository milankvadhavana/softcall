import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

# Make drf_spectacular optional — if not installed, @extend_schema becomes a no-op
try:
    from drf_spectacular.utils import (
        extend_schema, OpenApiParameter,
        OpenApiExample, OpenApiResponse
    )
    from drf_spectacular.types import OpenApiTypes
except ImportError:
    def extend_schema(**kwargs):
        def decorator(func):
            return func
        return decorator
    OpenApiParameter = None
    OpenApiExample = None
    OpenApiResponse = None
    OpenApiTypes = None

from .models import CustomUser, ContactData
from .serializers import (
    AdminCreateSerializer, AdminDetailSerializer,
    UserCreateSerializer, UserDetailSerializer,
    LoginSerializer, StatusUpdateSerializer,
    ContactCreateSerializer, ContactDetailSerializer,
)
from .permissions import IsSuperadmin, IsAdmin, IsAuthenticatedUser


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


# ════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════

class LoginView(APIView):
    permission_classes = []

    @extend_schema(
        tags        = ['Auth'],
        summary     = 'Login',
        description = 'Login with mobile + password. Returns JWT access & refresh tokens.',
        request     = LoginSerializer,
        responses   = {
            200: OpenApiResponse(description='Login successful — returns tokens + user info'),
            401: OpenApiResponse(description='Invalid mobile or password'),
            403: OpenApiResponse(description='Account inactive or plan expired'),
        },
        examples=[
            OpenApiExample(
                'Admin Login',
                value={'mobile': '9876543210', 'password': 'yourpassword'},
                request_only=True,
            ),
            OpenApiExample(
                'Success Response',
                value={
                    'message': 'Login successful.',
                    'role'   : 'admin',
                    'user'   : {'id': 1, 'name': 'Nikhil Gupta', 'email': 'nikhil@gmail.com', 'mobile': '9876543210'},
                    'tokens' : {'access': 'eyJ0eXAiOiJKV1Q...', 'refresh': 'eyJ0eXAiOiJKV1Q...'},
                },
                response_only=True, status_codes=['200'],
            ),
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        mobile   = serializer.validated_data['mobile']
        password = serializer.validated_data['password']

        try:
            user = CustomUser.objects.get(mobile=mobile)
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid mobile number or password."}, status=401)

        if not user.check_password(password):
            return Response({"error": "Invalid mobile number or password."}, status=401)

        if not user.is_account_active:
            return Response({"error": "Account inactive or plan expired."}, status=403)

        return Response({
            "message": "Login successful.",
            "role"   : user.role,
            "user"   : {"id": user.id, "name": user.name, "email": user.email, "mobile": user.mobile},
            "tokens" : get_tokens(user)
        })


# ════════════════════════════════════════════════════
#  SUPERADMIN — Admin Management
# ════════════════════════════════════════════════════

class AdminListCreateView(APIView):
    permission_classes = [IsSuperadmin]

    @extend_schema(
        tags='Superadmin', summary='List all admins',
        description='Get all admin accounts. **Superadmin only.**',
        responses={200: AdminDetailSerializer(many=True)},
    )
    def get(self, request):
        admins = CustomUser.objects.filter(role='admin').order_by('-created_at')
        return Response(AdminDetailSerializer(admins, many=True).data)

    @extend_schema(
        tags='Superadmin', summary='Create admin',
        description='Create a new admin with plan dates. **Superadmin only.**',
        request=AdminCreateSerializer,
        responses={201: AdminDetailSerializer, 400: OpenApiResponse(description='Validation error')},
        examples=[OpenApiExample('Create Admin', request_only=True, value={
            'name': 'Nikhil Gupta', 'email': 'nikhil@gmail.com', 'mobile': '9876543210',
            'password': 'pass1234', 'company': 'ABC Corp',
            'plan_start': '2026-01-01', 'plan_end': '2026-12-31', 'status': 'active'
        })],
    )
    def post(self, request):
        serializer = AdminCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        if CustomUser.objects.filter(email=serializer.validated_data.get('email')).exists():
            return Response({"error": "Email already registered."}, status=400)
        if CustomUser.objects.filter(mobile=serializer.validated_data.get('mobile')).exists():
            return Response({"error": "Mobile already registered."}, status=400)
        admin = serializer.save()
        admin.created_by = request.user
        admin.save()
        return Response({"message": "Admin created.", "admin": AdminDetailSerializer(admin).data}, status=201)


class AdminDetailView(APIView):
    permission_classes = [IsSuperadmin]

    def get_object(self, pk):
        try:    return CustomUser.objects.get(pk=pk, role='admin')
        except: return None

    @extend_schema(tags='Superadmin', summary='Get admin', responses={200: AdminDetailSerializer})
    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        return Response(AdminDetailSerializer(obj).data)

    @extend_schema(tags='Superadmin', summary='Update admin',
                   request=AdminCreateSerializer, responses={200: AdminDetailSerializer})
    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        s = AdminCreateSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response({"message": "Admin updated.", "admin": AdminDetailSerializer(obj).data})
        return Response(s.errors, status=400)

    @extend_schema(tags='Superadmin', summary='Delete admin',
                   responses={200: OpenApiResponse(description='Deleted')})
    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        obj.delete()
        return Response({"message": "Admin deleted."})


class AdminStatusView(APIView):
    permission_classes = [IsSuperadmin]

    @extend_schema(
        tags='Superadmin', summary='Change admin status',
        request=StatusUpdateSerializer, responses={200: AdminDetailSerializer},
        examples=[OpenApiExample('Set inactive', value={'status': 'inactive'}, request_only=True)],
    )
    def patch(self, request, pk):
        try:    obj = CustomUser.objects.get(pk=pk, role='admin')
        except: return Response({"error": "Not found."}, status=404)
        s = StatusUpdateSerializer(data=request.data)
        if s.is_valid():
            obj.status = s.validated_data['status']
            obj.save()
            return Response({"message": f"Status → {obj.status}", "admin": AdminDetailSerializer(obj).data})
        return Response(s.errors, status=400)


class AllUsersView(APIView):
    permission_classes = [IsSuperadmin]

    @extend_schema(
        tags='Superadmin', summary='List ALL users (across all admins)',
        responses={200: UserDetailSerializer(many=True)},
    )
    def get(self, request):
        users = CustomUser.objects.filter(role='user').order_by('-created_at')
        return Response(UserDetailSerializer(users, many=True).data)


# ════════════════════════════════════════════════════
#  ADMIN — Dashboard
# ════════════════════════════════════════════════════

class AdminDashboardView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags='Admin', summary='Admin dashboard',
        description='Returns admin stats — user count, contact count, per-user breakdown. **Admin only.**',
        responses={200: OpenApiResponse(description='Dashboard stats + user contact summary')},
    )
    def get(self, request):
        admin    = request.user
        users    = CustomUser.objects.filter(role='user', created_by=admin)
        contacts = ContactData.objects.filter(added_by=admin)

        return Response({
            "admin": {
                "id": admin.id, "name": admin.name, "email": admin.email,
                "mobile": admin.mobile, "company": admin.company,
                "plan_start": admin.plan_start, "plan_end": admin.plan_end,
                "plan_active": admin.is_plan_active,
            },
            "stats": {
                "total_users"   : users.count(),
                "active_users"  : users.filter(status='active').count(),
                "total_contacts": contacts.count(),
            },
            "users": [
                {
                    "user_id"       : u.id,
                    "user_name"     : u.name,
                    "user_email"    : u.email,
                    "user_mobile"   : u.mobile,
                    "user_status"   : u.status,
                    "total_contacts": contacts.filter(assigned_to=u).count(),
                }
                for u in users
            ],
        })


# ════════════════════════════════════════════════════
#  ADMIN — User Management
# ════════════════════════════════════════════════════

class UserListCreateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags='Admin', summary='List my users',
        description='All users created by this admin. **Admin only.**',
        responses={200: UserDetailSerializer(many=True)},
    )
    def get(self, request):
        users = CustomUser.objects.filter(role='user', created_by=request.user).order_by('-created_at')
        return Response(UserDetailSerializer(users, many=True).data)

    @extend_schema(
        tags='Admin', summary='Create user',
        request=UserCreateSerializer, responses={201: UserDetailSerializer},
        examples=[OpenApiExample('Create User', request_only=True, value={
            'name': 'Ritesh Shah', 'email': 'ritesh@gmail.com',
            'mobile': '9123456789', 'password': 'pass1234', 'status': 'active'
        })],
    )
    def post(self, request):
        s = UserCreateSerializer(data=request.data, context={'request': request})
        if not s.is_valid(): return Response(s.errors, status=400)
        if CustomUser.objects.filter(email=s.validated_data.get('email')).exists():
            return Response({"error": "Email already registered."}, status=400)
        if CustomUser.objects.filter(mobile=s.validated_data.get('mobile')).exists():
            return Response({"error": "Mobile already registered."}, status=400)
        user = s.save()
        return Response({"message": "User created.", "user": UserDetailSerializer(user).data}, status=201)


class UserDetailView(APIView):
    permission_classes = [IsAdmin]

    def get_object(self, pk, admin):
        try:    return CustomUser.objects.get(pk=pk, role='user', created_by=admin)
        except: return None

    @extend_schema(tags='Admin', summary='Get user', responses={200: UserDetailSerializer})
    def get(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj: return Response({"error": "Not found."}, status=404)
        return Response(UserDetailSerializer(obj).data)

    @extend_schema(tags='Admin', summary='Update user',
                   request=UserCreateSerializer, responses={200: UserDetailSerializer})
    def put(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj: return Response({"error": "Not found."}, status=404)
        s = UserCreateSerializer(obj, data=request.data, partial=True, context={'request': request})
        if s.is_valid():
            s.save()
            return Response({"message": "User updated.", "user": UserDetailSerializer(obj).data})
        return Response(s.errors, status=400)

    @extend_schema(tags='Admin', summary='Delete user',
                   responses={200: OpenApiResponse(description='Deleted')})
    def delete(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj: return Response({"error": "Not found."}, status=404)
        obj.delete()
        return Response({"message": "User deleted."})


class UserStatusView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags='Admin', summary='Change user status',
        request=StatusUpdateSerializer, responses={200: UserDetailSerializer},
        examples=[OpenApiExample('Set inactive', value={'status': 'inactive'}, request_only=True)],
    )
    def patch(self, request, pk):
        try:    obj = CustomUser.objects.get(pk=pk, role='user', created_by=request.user)
        except: return Response({"error": "Not found."}, status=404)
        s = StatusUpdateSerializer(data=request.data)
        if s.is_valid():
            obj.status = s.validated_data['status']
            obj.save()
            return Response({"message": f"Status → {obj.status}", "user": UserDetailSerializer(obj).data})
        return Response(s.errors, status=400)


# ════════════════════════════════════════════════════
#  ADMIN — Contact Management
# ════════════════════════════════════════════════════

class AdminContactListCreateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags='Admin', summary='List my contacts',
        description='All contacts added by this admin. Filter by `?user_id=3`. **Admin only.**',
        parameters=[
            OpenApiParameter('user_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Filter by assigned user ID', required=False),
        ],
        responses={200: ContactDetailSerializer(many=True)},
    )
    def get(self, request):
        qs      = ContactData.objects.filter(added_by=request.user)
        user_id = request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(assigned_to__id=user_id)
        return Response(ContactDetailSerializer(qs, many=True).data)

    @extend_schema(
        tags='Admin', summary='Add single contact',
        request=ContactCreateSerializer, responses={201: ContactDetailSerializer},
        examples=[OpenApiExample('Add Contact', request_only=True, value={
            'assigned_to': 3, 'name': 'John Doe',
            'contact_number': '9876543210', 'email': 'john@gmail.com'
        })],
    )
    def post(self, request):
        s = ContactCreateSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            contact = s.save()
            return Response({"message": "Contact added.", "contact": ContactDetailSerializer(contact).data}, status=201)
        return Response(s.errors, status=400)


class AdminContactDetailView(APIView):
    permission_classes = [IsAdmin]

    def get_object(self, pk, admin):
        try:    return ContactData.objects.get(pk=pk, added_by=admin)
        except: return None

    @extend_schema(tags='Admin', summary='Get contact', responses={200: ContactDetailSerializer})
    def get(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj: return Response({"error": "Not found."}, status=404)
        return Response(ContactDetailSerializer(obj).data)

    @extend_schema(tags='Admin', summary='Update contact',
                   request=ContactCreateSerializer, responses={200: ContactDetailSerializer})
    def put(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj: return Response({"error": "Not found."}, status=404)
        s = ContactCreateSerializer(obj, data=request.data, partial=True, context={'request': request})
        if s.is_valid():
            s.save()
            return Response({"message": "Contact updated.", "contact": ContactDetailSerializer(obj).data})
        return Response(s.errors, status=400)

    @extend_schema(tags='Admin', summary='Delete contact',
                   responses={200: OpenApiResponse(description='Deleted')})
    def delete(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj: return Response({"error": "Not found."}, status=404)
        obj.delete()
        return Response({"message": "Contact deleted."})


class AdminBulkUploadView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags='Admin',
        summary='Bulk upload contacts (CSV / Excel)',
        description='''
Upload a `.csv` or `.xlsx` file to create many contacts at once.

**Required columns:** `name`, `contact_number`
**Optional column:** `email`

**Form fields:**
- `file` — the CSV/Excel file
- `assigned_to` — ID of the user to assign all contacts to
        ''',
        request={
            'multipart/form-data': {
                'type'      : 'object',
                'properties': {
                    'file'       : {'type': 'string', 'format': 'binary', 'description': '.csv or .xlsx file'},
                    'assigned_to': {'type': 'integer', 'description': 'User ID to assign contacts to'},
                },
                'required': ['file', 'assigned_to'],
            }
        },
        responses={
            201: OpenApiResponse(description='Upload result: success_count, failed_count'),
            400: OpenApiResponse(description='Invalid file or missing required columns'),
        },
    )
    def post(self, request):
        file        = request.FILES.get('file')
        assigned_to = request.data.get('assigned_to')

        if not file:        return Response({"error": "No file provided."}, status=400)
        if not assigned_to: return Response({"error": "assigned_to is required."}, status=400)

        try:
            target = CustomUser.objects.get(pk=assigned_to, role='user', created_by=request.user)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found or not under your account."}, status=404)

        fname = file.name.lower()
        try:
            df = pd.read_csv(file) if fname.endswith('.csv') else pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Cannot read file: {e}"}, status=400)

        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        if not {'name', 'contact_number'}.issubset(set(df.columns)):
            return Response({"error": "File must have columns: name, contact_number (email optional)"}, status=400)

        contacts, skipped = [], 0
        for _, row in df.iterrows():
            name  = str(row.get('name', '')).strip()
            phone = str(row.get('contact_number', '')).strip()
            email = str(row.get('email', '')).strip() if 'email' in df.columns else ''
            if not name or name == 'nan' or not phone or phone == 'nan':
                skipped += 1; continue
            contacts.append(ContactData(
                added_by=request.user, assigned_to=target,
                name=name, contact_number=phone,
                email=email if email and email != 'nan' else None,
            ))

        ContactData.objects.bulk_create(contacts)
        return Response({
            "message"      : f"Upload done. {len(contacts)} added, {skipped} skipped.",
            "success_count": len(contacts),
            "failed_count" : skipped,
            "assigned_to"  : target.name,
        }, status=201)


class AdminContactDownloadTemplateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags='Admin', summary='Download Excel template',
        description='Download a sample .xlsx file with correct column headers for bulk upload.',
        responses={200: OpenApiResponse(description='Excel file (.xlsx)')},
    )
    def get(self, request):
        import openpyxl
        from django.http import HttpResponse
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Contacts"
        for col, h in enumerate(['name', 'contact_number', 'email'], 1):
            ws.cell(row=1, column=col, value=h).font = openpyxl.styles.Font(bold=True)
        ws.append(['John Doe',   '9876543210', 'john@example.com'])
        ws.append(['Jane Smith', '9123456789', ''])
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="contacts_template.xlsx"'
        wb.save(response)
        return response


# ════════════════════════════════════════════════════
#  USER — View contacts
# ════════════════════════════════════════════════════

class UserContactListView(APIView):
    permission_classes = [IsAuthenticatedUser]

    @extend_schema(
        tags='User', summary='My contacts',
        description='Returns only contacts assigned to the logged-in user. **User only.**',
        responses={200: ContactDetailSerializer(many=True)},
    )
    def get(self, request):
        contacts = ContactData.objects.filter(assigned_to=request.user)
        return Response({
            "total"   : contacts.count(),
            "contacts": ContactDetailSerializer(contacts, many=True).data
        })


class UserContactDetailView(APIView):
    permission_classes = [IsAuthenticatedUser]

    @extend_schema(
        tags='User', summary='Get single contact',
        description='View one contact — only if it belongs to the logged-in user. **User only.**',
        responses={200: ContactDetailSerializer, 404: OpenApiResponse(description='Not found or not yours')},
    )
    def get(self, request, pk):
        try:
            contact = ContactData.objects.get(pk=pk, assigned_to=request.user)
        except ContactData.DoesNotExist:
            return Response({"error": "Contact not found."}, status=404)
        return Response(ContactDetailSerializer(contact).data)