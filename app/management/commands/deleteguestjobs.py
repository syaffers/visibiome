from app.models import BiomSearchJob, Guest
from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz

class Command(BaseCommand):
    help = "Deletes all guest-initiated jobs which are k days old,\
            finished or unfinished"

    def handle(self, *args, **options):
        k = 1
        now = timezone.now()
        guests = Guest.objects.filter(status=1)

        self.stdout.write(self.style.SUCCESS(
            'Started cron job on %s' % now.ctime()))

        for guest in guests:
            jobs = BiomSearchJob.objects.filter(user_id=guest.user)

            for job in jobs:
                threshold = k * 24 * 60 * 60
                time_diff = now - job.created_at
                data_tuple = (job.pk, job.user_id, time_diff.total_seconds())

                if time_diff.total_seconds() > threshold:
                    self.stdout.write(self.style.SUCCESS(
                        'Deleted job %d from user %d: %f' % data_tuple))
                    job.delete()
