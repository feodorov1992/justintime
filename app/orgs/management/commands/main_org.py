import json

from django.core.management.base import BaseCommand

from orgs.models import Organisation


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('config', help='Path to JSON config with company requisites')

    def handle(self, *args, **options):
        config_path = options.get('config')
        with open(config_path) as file:
            config = json.load(file)
        Organisation.objects.create(is_expeditor=True, **config)
