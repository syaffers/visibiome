# Visibiome: Microbiome Search and Visualization Tool #

## Setup ##
1. Start a VM or EC2 server with QIIME pre-installed.

2. Clone this repository

        $ git clone https://syaffers@bitbucket.org/syaffers/visibiome.git
        $ cd visibiome


3. Install app dependencies

        $ pip install -r requirements.txt


4. Migrate and populate database (delete current DB to start fresh)

        $ python manage.py migrate
        $ python manage.py loaddata data/ecosystem_choices.json

5. Create a superuser (optional, but useful!)

        $ python manage.py createsuperuser

6. Setup a Redis cache (try RedisLabs, AWS ElastiCache is a little difficult to
configure)

7. Edit `app/settings.py` to include Redis server URL by editing the following
line

        ...
        BROKER_URL = "redis://<REDIS_IP_ADDRESS>//"
        ...

8. Update `settings.py` to match current Microbiome DB service

        ...
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
        ...

9. Set public directories by editing the `MEDIA_ROOT` and `LARGE_DATA_PATH`

        ...
        MEDIA_ROOT = '/path/to/user/writable/directory/media'
        ...
        LARGE_DATA_PATH = '/path/to/user/writable/directory/data'
        ...

10. Make the two folders with the paths you just assigned to the public
directories

        $ mkdir /path/to/user/writable/directory/media
        $ mkdir /path/to/user/writable/directory/data

11. Copy the 10k files into the `/path/to/user/writable/directory/data`
directory

12. Run `python manage.py collectstatic` to move the static files to a preset
location

### Optional settings for production
12. Edit the `uwsgi.ini` file to configure logging and development server
details (optional)

12. Update celery settings to point to current deployment type (optional).
Possible deployment types: `local` (default), `development`, `production`

12. Make sure `mod_wsgi` is installed and enabled on your system

        $ sudo apt-get install libapache2-mod-wsgi
        $ sudo a2enmod wsgi

## Running a local server_password
12. Start worker

        $ celery -A darp worker

13. Start `local` server

        $ python manage.py runserver 0.0.0.0:8000

14. Hope for the best 😎

## Running a development or production server
14. Start `development` or `production` server

        $ uwsgi --ini uwsgi.ini

14. Hope for the best 😎
