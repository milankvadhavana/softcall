from rest_framework import serializers
from .models import CustomUser , ContactData
from django.utils import timezone


class LoginSerializer(serializers.Serializer):
    mobile = serializers.CharField(required=True, max_length=15)
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    def validate_mobile(self, value):
        if not value.strip():
            raise serializers.ValidationError("Mobile number cannot be empty.")
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain only digits.")
        return value.strip()


class AdminCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Admin users"""
    
    class Meta:
        model = CustomUser
        fields = ['email', 'mobile', 'name', 'password', 'company', 'plan_start', 'plan_end', 'status']
        extra_kwargs = {
            'password': {'write_only': True},
            'company': {'required': True},
            'plan_start': {'required': True},
            'plan_end': {'required': True},
        }
    
    def validate(self, data):
        """Validate plan dates"""
        plan_start = data.get('plan_start')
        plan_end = data.get('plan_end')
        
        if plan_start and plan_end:
            if plan_end <= plan_start:
                raise serializers.ValidationError({
                    'plan_end': 'Plan end date must be after plan start date.'
                })
        
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create(
            role='admin',
            is_staff=False,
            is_active=True,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class AdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying Admin details"""
    plan_active = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'mobile', 'name', 'company', 
            'plan_start', 'plan_end', 'status', 'plan_active',
            'created_at', 'updated_at'
        ]
    
    def get_plan_active(self, obj):
        return obj.is_plan_active


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating User (by Admin)"""
    
    class Meta:
        model = CustomUser
        fields = ['email', 'mobile', 'name', 'password', 'status']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        request = self.context.get('request')
        
        user = CustomUser.objects.create(
            role='user',
            created_by=request.user if request else None,
            is_staff=False,
            is_active=True,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying User details"""
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'mobile', 'name', 'status',
            'created_by_name', 'created_at', 'updated_at'
        ]

# Contact data serializer
class ContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ContactData
        fields = ['id', 'assigned_to', 'name', 'contact_number', 'email']

    def validate_assigned_to(self, user):
        request = self.context.get('request')
        # Admin can only assign to users he created
        if user.created_by != request.user:
            raise serializers.ValidationError(
                "You can only assign contacts to users you created."
            )
        if user.role != 'user':
            raise serializers.ValidationError("assigned_to must be a User.")
        return user

    def create(self, validated_data):
        validated_data['added_by'] = self.context['request'].user
        return super().create(validated_data)


class ContactDetailSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True)
    added_by_name    = serializers.CharField(source='added_by.name',    read_only=True)

    class Meta:
        model  = ContactData
        fields = [
            'id', 'name', 'contact_number', 'email',
            'assigned_to', 'assigned_to_name',
            'added_by_name', 'created_at'
        ]


class BulkUploadResponseSerializer(serializers.Serializer):
    total_rows    = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count  = serializers.IntegerField()
    errors        = serializers.ListField(child=serializers.DictField())


class StatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating status"""
    status = serializers.ChoiceField(choices=['active', 'inactive'])