from django.conf import settings
server_db = dict(
    db=settings.DATABASES['microbiome']['NAME'],
    host=settings.DATABASES['microbiome']['HOST'],
    user=settings.DATABASES['microbiome']['USER'],
    passwd=settings.DATABASES['microbiome']['PASSWORD'],
)
