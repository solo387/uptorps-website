from django.core.management.base import BaseCommand
from wallet.models import Wallet
from accounts.models import User

class Command(BaseCommand):
    help = 'Seed the database with initial wallets'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Wallets...')

        try:
            premium_wallet= User.objects.get(email='premium_wallet@uptorps.com', username='premium_wallet.sys')
            referral_wallet= User.objects.get(email='referral_wallet@uptorps.com', username='referral_wallet.sys')
            reward_scheme_wallet= User.objects.get(email='reward_scheme_wallet@uptorps.com', username='reward_scheme_wallet.sys')
            ceo_wallet= User.objects.get(email='ceo_wallet@uptorps.com', username='ceo_wallet.sys')
            maintenance_wallet= User.objects.get(email='maintenance_wallet@uptorps.com', username='maintenance_wallet.sys')
            workers_wallet= User.objects.get(email='workers_wallet@uptorps.com', username='workers_wallet.sys')
        except User.DoesNotExist:
            self.stdout.write('Something went wrong make sure user account\'s exist.....')
            return
        # 1. Define Wallets
        wallets_data = [
            {'user': premium_wallet},
            {'user': referral_wallet},
            {'user': reward_scheme_wallet},
            {'user': ceo_wallet},
            {'user': maintenance_wallet},
            {'user': workers_wallet},
        ]

        # Create Wallet
        created_wallet = {}
        for wallt_data in wallets_data:
            wallet, created = Wallet.objects.get_or_create(
                user=wallt_data['user'],
            )
            created_wallet[wallet.user] = wallet
            if created:
                self.stdout.write(self.style.SUCCESS(f'Wallet created: {wallet.user}'))

        self.stdout.write(self.style.SUCCESS('Seeding completed successfully!'))