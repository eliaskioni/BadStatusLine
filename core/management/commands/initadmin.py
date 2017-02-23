from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument('--username',
                            dest='username',
                            default='admin',
                            help=('super user admin'))
        parser.add_argument('--password',
                            help=("enter username"),
                            )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options.get('email', 'admin@example.com')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
