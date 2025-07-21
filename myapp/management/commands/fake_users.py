from django.core.management.base import BaseCommand
from myapp.models import CustomUser
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Create 20 fake Kenyan users'

    def handle(self, *args, **kwargs):
        faker = Faker('en_US')
        user_types = ['staff', 'member']

        for i in range(20):
            email = f"user{i}@example.com"
            first_name = faker.first_name()
            last_name = faker.last_name()
            password = "password123"

            CustomUser.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                is_verified=True
            )
        
        self.stdout.write(self.style.SUCCESS("✅ 20 fake users created successfully."))
