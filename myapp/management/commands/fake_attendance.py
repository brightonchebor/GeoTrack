from django.core.management.base import BaseCommand
from myapp.models import CustomUser, Attendance
from faker import Faker
import random
from datetime import datetime, timedelta, time, date

class Command(BaseCommand):
    help = 'Create fake attendance records for users'

    def handle(self, *args, **kwargs):
        faker = Faker()
        users = CustomUser.objects.filter(is_active=True)

        today = date.today()

        for user in users:
            # Choose a random date in the last 14 days
            for _ in range(random.randint(5, 10)):  # 5–10 days of attendance
                random_days_ago = random.randint(1, 14)
                attend_date = today - timedelta(days=random_days_ago)

                # Skip if record already exists for that date
                if Attendance.objects.filter(user=user, date=attend_date).exists():
                    continue

                # Check-in: between 7:00 and 9:00 AM
                checkin_time = datetime.combine(attend_date, time(random.randint(7, 9), random.randint(0, 59)))

                # Check-out: between 4:00 and 6:00 PM
                checkout_time = datetime.combine(attend_date, time(random.randint(16, 18), random.randint(0, 59)))

                Attendance.objects.create(
                    user=user,
                    date=attend_date,
                    checkin_time=checkin_time,
                    checkout_time=checkout_time
                )

        self.stdout.write(self.style.SUCCESS("✅ Fake attendance records created."))
