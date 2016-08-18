# Local server settings - unsuitable for production. Use these settings
# when you are testing on your personal computer and are making rapid,
# potentially fatal changes and testing new ideas.

from vzb.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret! It's okay
# here for now
SECRET_KEY = 'k&9nph7dp%1v1_e0t@()=fbs*vl2*i0=r2hdt-m)c#&nt2^yh*'

# I want to see debug messages when developing stuff on my computer. Turning the
# flag to False requires you to setup the static files path and media path.
# Maybe keep it like this until you know what you're doing.
DEBUG = True

# Allowed hosts can be empty since we're only serving locally to our computer
ALLOWED_HOSTS = []

# Log to console for local servers, easier to immediately see errors
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

# Use sqlite3 since it's easier to refresh and manage if problem occurs
# database should be located at visibiome/db.sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
        'USER': '',
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/qiime/www/staticfiles/media/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'app/static/'),
)

# Microbiome Database configuration
MICROBIOME_DB = {
    'NAME': 'ServerMicroBiome',
    # Currently it's pointing a local copy of the live microbiome database
    'HOST': 'localhost',
    'USER': 'root',
    # Consider placing the password in an environment variable for production
    'PASSWORD': 'qiime'
}

# The 10K matrix path. This is placed wherever you want as long as it is
# readable by the user deploying the webserver. Assuming you are using the
# Ubuntu VM provided by Qiime, the path should look something like below
TEN_K_DATA_PATH = '/home/qiime/www/staticfiles/data/'

# If you can host a redis on your machine, just use 127.0.0.1, else
# use an online one. If you can setup a redis on your home machine and is
# running a VM of Ubuntu with Qiime with VirtualBox, use 10.0.2.2
BROKER_URL = "redis://10.0.2.2//"
