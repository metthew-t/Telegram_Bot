from rest_framework import serializers
from .models import User, Case, Message, AuditLog, InternalMessage, AssignmentRequest, Feedback

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'telegram_id', 'email_verified', 'email_notifications_enabled', 'email_approved_by_owner', 'profile_photo', 'password']
        read_only_fields = ['id', 'email_verified']

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
    feedback = serializers.SerializerMethodField()
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
            'user_case_number',
            'created_at',
            'updated_at',
            'assigned_at',
            'resolved_at',
            'closed_at',
            'feedback',
        ]
        read_only_fields = ['id', 'user_case_number', 'created_at', 'updated_at', 'assigned_at', 'resolved_at', 'closed_at', 'feedback']

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
        
        # ── OWNERS AS ONE ENTITY: Show "All Owners" when assigned to any owner ──
        if obj.assigned_admin.role == 'owner':
            return {
                'id': obj.assigned_admin.id,
                'username': obj.assigned_admin.username,
                'label': 'All Owners',
                'role': 'owner'
            }
        
        if request.user.role == 'owner':
            return UserSerializer(obj.assigned_admin, context=self.context).data
        if request.user.role == 'admin':
            return {
                'id': obj.assigned_admin.id,
                'label': obj.assigned_admin.username,
            }
        return {'label': 'Assigned admin'}
    
    def get_feedback(self, obj):
        """Return feedback for this case if it exists"""
        try:
            # feedback is OneToOneField, access directly (not with .first())
            feedback = obj.feedback
            if feedback:
                return {
                    'id': feedback.id,
                    'content': feedback.content,
                    'rating': feedback.rating,
                    'created_at': feedback.created_at,
                }
        except Exception:
            # No feedback exists for this case
            pass
        return None

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    sender_profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'case', 'sender', 'sender_role', 'sender_profile_photo', 'content', 'message_type', 'voice_data', 'voice_duration', 'timestamp']
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
    
    def get_sender_profile_photo(self, obj):
        """Only show profile photo to staff (admin/owner), not to users"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role in ['admin', 'owner']:
            return obj.sender.profile_photo
        return None

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
    sender_profile_photo = serializers.ReadOnlyField(source='sender.profile_photo')

    class Meta:
        model = InternalMessage
        fields = ['id', 'sender', 'sender_name', 'sender_role', 'sender_profile_photo', 'content', 'message_type', 'message_format', 'voice_data', 'voice_duration', 'timestamp', 'file_name', 'file_content']
        read_only_fields = ['id', 'timestamp', 'sender']


class AssignmentRequestSerializer(serializers.ModelSerializer):
    admin_name = serializers.ReadOnlyField(source='admin.username')
    case_title = serializers.ReadOnlyField(source='case.title')
    case_id = serializers.ReadOnlyField(source='case.id')
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentRequest
        fields = ['id', 'case', 'case_id', 'case_title', 'admin', 'admin_name', 'status', 'created_at', 'reviewed_at', 'reviewed_by', 'reviewed_by_name']
        read_only_fields = ['id', 'created_at', 'reviewed_at', 'reviewed_by']

    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.username if obj.reviewed_by else None


class FeedbackSerializer(serializers.ModelSerializer):
    case_title = serializers.ReadOnlyField(source='case.title')
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ['id', 'case', 'case_title', 'user', 'user_name', 'content', 'rating', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_user_name(self, obj):
        """Protect user privacy - show as anonymous"""
        return 'Anonymous User'
