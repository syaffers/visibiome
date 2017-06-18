# Development server settings - unsuitable for production. Use these settings
# when you are testing on a cloud-deployed server but not to be viewed live
# (i.e. not production server).

from vzb.settings.base import *

# If this is not defined yet, define it in /etc/environment, then log out and
# log back in
# SECRET_KEY = os.environ.get('DJANGO_SECRETKEY')
SECRET_KEY = 'k&9nph7dp%1v1_e0t@()=fbs*vl2*i0=r2hdt-m)c#&nt2^yh*'

# I want to see debug messages when developing stuff on my computer. Turning the
# flag to False requires you to setup the static files path and media path.
# This is when you should try setting it to False to see how it works on a test
# server
DEBUG = False

# Allowed hosts can be empty if debug is True. Otherwise you must include the
# host IP or domain name in the list below
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

DATABASES = {
    'default': {
        # Django default development database
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': 'db.sqlite3',
        # 'USER': '',
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Visibiome',
        'USER': 'root',
        # Consider placing the password in an environment variable
        'PASSWORD': 'qiime',
        # Or an IP Address that your DB is hosted on
        'HOST': 'localhost',
        'PORT': '3306',
    },
    # Microbiome Database configuration. This database is not handled by
    # Django due to legacy reasons so no engine configuration needed.
    'microbiome': {
        'NAME': 'EarthMicroBiome',
        # Currently it's pointing to the old microbiome sevrer in an EC2
        'HOST': '52.33.150.116',
        'USER': 'syafiq',
        # Consider placing the password in an environment variable for
        # production
        'PASSWORD': 'syafiq123',
    }
}

# Log all the requests and (potential) errors to file
LOG_FILE = os.path.join(BASE_DIR, 'logs/vzb.log')
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
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles/')
# Static files are handled by whitenoise and hence doesn't need Apache's
# permissions. This reduces dependencies and configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')

# The 10K matrix path. This is placed wherever you want as long as it is
# readable by the user deploying the webserver. Assuming you are using an EC2
# server with the Qiime AMI, it should look something like the string below
L_MATRIX_DATA_PATH = os.path.join(STATIC_ROOT, 'data/')

# Use a live redis cache to do message queueing
# BROKER_URL = "redis://:pizzaisgreat@"\
#              "pub-redis-17533.us-east-1-4.3.ec2.garantiadata.com:17533"
BROKER_URL = "redis://127.0.0.1//"

# Set maximum number of uploadable samples in asingle BIOM file
MAX_NO_OF_SAMPLES = 50
