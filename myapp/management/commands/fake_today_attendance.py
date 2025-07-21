from django.core.management.base import BaseCommand
from myapp.models import CustomUser, Attendance
from faker import Faker
from datetime import datetime, time, date
import random

class Command(BaseCommand):
    help = 'Create fake check-in only attendance for first 10 members today'

    def handle(self, *args, **kwargs):
        faker = Faker()
        today = date.today()

        # Get first 10 members who are active
        members = CustomUser.objects.filter(user_type='member', is_active=True).order_by('id')[:10]

        count = 0
        for user in members:
            if Attendance.objects.filter(user=user, date=today).exists():
                continue
            # Random check-in between 7:00 AM and 9:00 AM
            checkin_time = datetime.combine(today, time(random.randint(7, 9), random.randint(0, 59)))

            Attendance.objects.create(
                user=user,
                date=today,
                checkin_time=checkin_time,
            )

            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {count} members checked in today."))
