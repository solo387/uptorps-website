from django.dispatch import Signal

# Fired when an admin is created
admin_created = Signal()

# Fired when a user is deleted
user_deleted = Signal()

# Fired when an admin login fails
failed_admin_login = Signal()

# Fired when adn admin login sucess
success_admin_login = Signal()