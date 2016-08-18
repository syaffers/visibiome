from django.conf import settings
server_db = dict(
    db=settings.MICROBIOME_DB['NAME'],
    host=settings.MICROBIOME_DB['HOST'],
    user=settings.MICROBIOME_DB['USER'],
    passwd=settings.MICROBIOME_DB['PASSWORD'],
)
