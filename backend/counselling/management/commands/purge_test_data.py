"""
Django management command to purge all test data before launch.
Usage: python manage.py purge_test_data --confirm

This command:
1. Keeps the Owner account(s) intact (role='owner' or username='owner').
2. Deletes all cases, case messages, internal messages, feedback, audit logs,
   case views, internal chat views, assignment requests, and password reset tokens.
3. Deletes all non-owner users (admins, counselors, telegram users).
4. Resets database auto-increment ID sequences so the next case starts at ID #1.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction, models
from django.contrib.auth import get_user_model
from counselling.models import (
    Case,
    Message,
    InternalMessage,
    AuditLog,
    CaseAssignmentRequest,
    Feedback,
    CaseView,
    InternalChatView,
    PasswordResetToken,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Purge all test data (cases, messages, non-owner users) and reset ID sequences for launch.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to wipe test data and reset sequences.',
        )

    def handle(self, *args, **options):
        if not options.get('confirm'):
            raise CommandError(
                "Safety guard: You must pass '--confirm' to execute this command.\n"
                "Example: python manage.py purge_test_data --confirm"
            )

        self.stdout.write("[INFO] Starting pre-launch test data purge...")

        # 1. Verify owner exists
        owners = User.objects.filter(models.Q(role='owner') | models.Q(username='owner'))
        if not owners.exists():
            # If no owner exists, create a default owner
            owner = User.objects.create(
                username='owner',
                email='owner@example.com',
                role='owner',
                email_verified=True,
            )
            owner.set_password('owner1234')
            owner.save()
            self.stdout.write("[OK] Created default owner: owner / owner1234.")
        else:
            # Ensure all identified owners have role='owner' and email_verified=True
            for o in owners:
                if o.role != 'owner' or not o.email_verified:
                    o.role = 'owner'
                    o.email_verified = True
                    o.save()

        owner_usernames = list(User.objects.filter(role='owner').values_list('username', flat=True))
        self.stdout.write(f"[INFO] Preserving Owner account(s): {', '.join(owner_usernames)}")

        # 2. Delete test data inside transaction
        with transaction.atomic():
            # Views & tracking
            c_views, _ = CaseView.objects.all().delete()
            ic_views, _ = InternalChatView.objects.all().delete()
            self.stdout.write(f"  * Deleted CaseView ({c_views}) and InternalChatView ({ic_views})")

            # Feedback & requests
            fb_count, _ = Feedback.objects.all().delete()
            req_count, _ = CaseAssignmentRequest.objects.all().delete()
            self.stdout.write(f"  * Deleted Feedback ({fb_count}) and CaseAssignmentRequest ({req_count})")

            # Messages
            msg_count, _ = Message.objects.all().delete()
            im_count, _ = InternalMessage.objects.all().delete()
            self.stdout.write(f"  * Deleted Case Messages ({msg_count}) and Internal Messages ({im_count})")

            # Audit logs
            audit_count, _ = AuditLog.objects.all().delete()
            self.stdout.write(f"  * Deleted AuditLog ({audit_count})")

            # Cases
            case_count, _ = Case.objects.all().delete()
            self.stdout.write(f"  * Deleted Cases ({case_count})")

            # Password reset tokens
            token_count, _ = PasswordResetToken.objects.all().delete()
            self.stdout.write(f"  * Deleted PasswordResetTokens ({token_count})")

            # Non-owner users
            non_owners = User.objects.exclude(models.Q(role='owner') | models.Q(username='owner'))
            user_count = non_owners.count()
            non_owners.delete()
            self.stdout.write(f"  * Deleted non-owner Users ({user_count})")

        # 3. Reset sequences
        self.reset_id_sequences()

        self.stdout.write(
            "[SUCCESS] All test data has been purged, Owner preserved, and ID sequences reset to 1!\n"
        )

    def reset_id_sequences(self):
        """Reset auto-increment sequences for both PostgreSQL and SQLite."""
        tables_to_restart = [
            'counselling_case',
            'counselling_message',
            'counselling_internalmessage',
            'counselling_caseassignmentrequest',
            'counselling_feedback',
            'counselling_caseview',
            'counselling_internalchatview',
            'counselling_auditlog',
            'counselling_passwordresettoken',
        ]

        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                self.stdout.write("[INFO] Resetting PostgreSQL sequences...")
                for table in tables_to_restart:
                    try:
                        cursor.execute(f"SELECT pg_get_serial_sequence('{table}', 'id');")
                        row = cursor.fetchone()
                        if row and row[0]:
                            seq_name = row[0]
                            cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1;")
                            self.stdout.write(f"  * Sequence for {table} restarted at 1 ({seq_name})")
                        else:
                            cursor.execute(f"ALTER TABLE {table} ALTER COLUMN id RESTART WITH 1;")
                            self.stdout.write(f"  * Identity column for {table} restarted at 1")
                    except Exception as e:
                        try:
                            cursor.execute(f"ALTER TABLE {table} ALTER COLUMN id RESTART WITH 1;")
                            self.stdout.write(f"  * Identity column fallback for {table} restarted at 1")
                        except Exception as e2:
                            self.stdout.write(f"  [WARN] Could not restart sequence for {table}: {e} / {e2}")

                # Adjust counselling_user sequence to MAX(id)
                try:
                    cursor.execute("SELECT pg_get_serial_sequence('counselling_user', 'id');")
                    row = cursor.fetchone()
                    cursor.execute("SELECT COALESCE(MAX(id), 1) FROM counselling_user;")
                    max_user_id = cursor.fetchone()[0] or 1
                    if row and row[0]:
                        user_seq = row[0]
                        cursor.execute(f"SELECT setval('{user_seq}', {max_user_id});")
                        self.stdout.write(f"  * Sequence for counselling_user set to {max_user_id}")
                except Exception as e:
                    self.stdout.write(f"  [WARN] Could not adjust counselling_user sequence: {e}")

            elif connection.vendor == 'sqlite':
                self.stdout.write("[INFO] Resetting SQLite sequences...")
                for table in tables_to_restart:
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name = %s;", [table])
                    self.stdout.write(f"  * Reset sqlite_sequence for {table}")

                cursor.execute("SELECT COALESCE(MAX(id), 1) FROM counselling_user;")
                max_user_id = cursor.fetchone()[0] or 1
                cursor.execute(
                    "UPDATE sqlite_sequence SET seq = %s WHERE name = 'counselling_user';",
                    [max_user_id]
                )
                self.stdout.write(f"  * sqlite_sequence for counselling_user set to {max_user_id}")
            else:
                self.stdout.write(f"[NOTICE] Sequence reset not required or unsupported for vendor: {connection.vendor}")
