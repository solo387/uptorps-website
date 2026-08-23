from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Seed the database with system users'

    def handle(self, *args, **options):
        self.stdout.write('Seeding System Users...')

        system_users = [
            {
                'email': 'premium_wallet@uptorps.com',
                'username': 'premium_wallet.sys',
                'role': User.Roles.SYS
            },
            {
                'email': 'referral_wallet@uptorps.com',
                'username': 'referral_wallet.sys',
                'role': User.Roles.SYS
            },
            {
                'email': 'reward_scheme_wallet@uptorps.com',
                'username': 'reward_scheme_wallet.sys',
                'role': User.Roles.SYS
            },
            {
                'email': 'ceo_wallet@uptorps.com',
                'username': 'ceo_wallet.sys',
                'role': User.Roles.SYS
            },
            {
                'email': 'maintenance_wallet@uptorps.com',
                'username': 'maintenance_wallet.sys',
                'role': User.Roles.SYS
            },
            {
                'email': 'workers_wallet@uptorps.com',
                'username': 'workers_wallet.sys',
                'role': User.Roles.SYS
            },
        ]

        for user_data in system_users:
            existing_user = User.objects.filter(email=...).first()

            if not existing_user:
                user = User(
                    email=user_data['email'],
                    role=user_data['role'],
                    username=user_data['username'],
                    is_staff=False,
                    is_superuser=False,
                    is_active=True,
                    email_verified=True,
                )
                user.set_unusable_password()
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'System user created: {user.username}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'System user already exists: {user.username}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS('System user seeding completed successfully!')
        )