# Development server settings - unsuitable for production. Use these settings
# when you are testing on a cloud-deployed server but not to be viewed live
# (i.e. not production server).

from vzb.settings.base import *

# If this is not defined yet, define it in /etc/environment, then log out and
# log back in
SECRET_KEY = os.environ.get('DJANGO_SECRETKEY')

# I want to see debug messages when developing stuff on my computer. Turning the
# flag to False requires you to setup the static files path and media path.
# This is when you should try setting it to False to see how it works on a test
# server
DEBUG = True

# Allowed hosts can be empty since debug is True
ALLOWED_HOSTS = []

# Use sqlite3 since it's easier to refresh and manage if problem occurs
# database should be located at visibiome/db.sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
        'USER': '',
    }
}

# Log all the requests and (potential) errors to file
LOG_FILE = BASE_DIR + 'vzb_dev.log'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/qiime/www/staticfiles/media/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'app/static/'),
)

# Microbiome Database configuration.
MICROBIOME_DB = {
    'NAME': 'ServerMicroBiome',
    # Currently it's pointing to the old microbiome sevrer in an EC2
    'HOST': '52.33.150.116',
    'USER': 'syafiq',
    # Consider placing the password in an environment variable for production
    'PASSWORD': 'syafiq123'
}

# The 10K matrix path. This is placed wherever you want as long as it is
# readable by the user deploying the webserver. Assuming you are using an EC2
# server with the Qiime AMI, it should look something like the string below
TEN_K_DATA_PATH = '/home/ubuntu/www/staticfiles/data/'

# Use a live redis cache to do message queueing
BROKER_URL = "redis://:pizzaisgreat@"\
             "pub-redis-17533.us-east-1-4.3.ec2.garantiadata.com:17533"
