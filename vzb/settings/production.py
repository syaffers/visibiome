# Production server settings - suitable for production. Use these settings
# when you are running the site on a cloud-deployed server live. Exercise extra
# caution. Golden rule: you can never be too careful with security.
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

from vzb.settings.base import *

# If this is not defined yet, define it in /etc/environment, then log out and
# log back in.
SECRET_KEY = os.environ.get('DJANGO_SECRETKEY')

# Do not debug!
DEBUG = False

# Allowed hosts cannot be empty. We should really only allow 'localhost' and
# loopback (i.e. '127.0.0.1') and maybe even the EC2 IP address.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Use whatever database you want for production, could be MySQL, PostgreSQL,
# MSSQL, Oracle, etc. Read https://docs.djangoproject.com/en/1.9/ref/databases/
# for more information regarding setting up your own DBMS. Do NOT use sqlite!
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Visibiome',
        'USER': 'root',
        # Consider placing the password in an environment variable
        'PASSWORD': os.environ['VZB_DB_PASSWORD'],
        # Or an IP Address that your DB is hosted on
        'HOST': 'localhost',
        'PORT': '3306',
    },
    # Microbiome Database configuration. This database is not handled by
    # Django due to legacy reasons so no engine configuration needed.
    'microbiome': {
        'NAME': 'ServerMicroBiome',
        # Currently it's pointing to the old microbiome sevrer in an EC2
        'HOST': '52.33.150.116',
        'USER': 'syafiq',
        # Consider placing the password in an environment variable for
        # production
        'PASSWORD': 'syafiq123',
    }
}

# Log everything!
LOG_FILE = BASE_DIR + '/vzb_prd.log'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
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

# The 10K matrix path. This is placed wherever you want as long as it is
# readable by the user deploying the webserver. Assuming you are using an EC2
# server with the Qiime AMI, it should look something like the string below
TEN_K_DATA_PATH = '/home/ubuntu/www/staticfiles/data/10k'

# Use a live redis cache to do message queueing. Consider putting the password
# to the redis server in an environment variable
BROKER_URL = "redis://:pizzaisgreat@"\
             "pub-redis-17533.us-east-1-4.3.ec2.garantiadata.com:17533"
