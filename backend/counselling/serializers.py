from rest_framework import serializers
from .models import User, Case, Message, AuditLog, InternalMessage

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'telegram_id', 'password']
        read_only_fields = ['id']

    def validate_role(self, value):
        request = self.context.get('request')
        # Allow anyone to register as 'admin' or 'user'
        # Only existing owners can create/assign the 'owner' role
        if value == 'owner' and not (request and request.user.is_authenticated and request.user.role == 'owner'):
            raise serializers.ValidationError('Only an existing owner can assign the owner role.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.role != 'owner':
            data.pop('telegram_id', None)
        return data

class CaseSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    assigned_admin = serializers.SerializerMethodField()
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='user'),
        source='user',
        write_only=True,
        required=False,
    )
    assigned_admin_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='admin'),
        source='assigned_admin',
        write_only=True,
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            'id',
            'title',
            'description',
            'status',
            'user',
            'assigned_admin',
            'user_id',
            'assigned_admin_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {'label': 'Anonymous'}
        if request.user.role == 'owner':
            return UserSerializer(obj.user, context=self.context).data
        if obj.user == request.user:
            return {'label': 'You'}
        return {'label': f'User #{obj.user.id}'}

    def get_assigned_admin(self, obj):
        if obj.assigned_admin is None:
            return None
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {'label': 'Assigned admin'}
        if request.user.role == 'owner':
            return UserSerializer(obj.assigned_admin, context=self.context).data
        if request.user.role == 'admin':
            return {
                'id': obj.assigned_admin.id,
                'label': obj.assigned_admin.username,
            }
        return {'label': 'Assigned admin'}

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'case', 'sender', 'sender_role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp']

    def get_sender(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'owner':
            return UserSerializer(obj.sender, context=self.context).data
        if request and obj.sender == request.user:
            return {'label': 'You'}
        if obj.sender.role in ['admin', 'owner']:
            return {'label': 'Support team'}
        return {'label': 'Anonymous user'}

    def get_sender_role(self, obj):
        return obj.sender.role

class AuditLogSerializer(serializers.ModelSerializer):
    performer = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ['id', 'case', 'action', 'details', 'performer', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_performer(self, obj):
        request = self.context.get('request')
        if obj.performer is None:
            return {'label': 'System'}
        if request and request.user.is_authenticated and request.user.role == 'owner':
            return UserSerializer(obj.performer, context=self.context).data
        return {'label': obj.performer.username}
class InternalMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_role = serializers.ReadOnlyField(source='sender.role')

    class Meta:
        model = InternalMessage
        fields = ['id', 'sender', 'sender_name', 'sender_role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'sender']
