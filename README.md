# Visibiome: Microbiome Search and Visualization Tool #

## Setup ##
1. Start a VM or EC2 server with QIIME pre-installed.

2. Clone this repository

        $ git clone https://syaffers@bitbucket.org/syaffers/visibiome.git
        $ cd visibiome

3. Install app dependencies

        $ pip install -r requirements.txt

4. Migrate and populate database. Clear (or delete) the current database to
start with a fresh installation. Change `<SETTING>` to your current
deployment settings (e.g. `local`, `deployment`, `production`)

        $ python manage.py migrate --settings=vzb.settings.<SETTING>
        $ python manage.py loaddata data/ecosystem_choices.json --settings=vzb.settings.<SETTING>

5. Create a superuser (optional, but useful!). Change `--settings=` to your
current deployment settings

        $ python manage.py createsuperuser --settings=vzb.settings.<SETTING>

6. Setup a Redis cache. For distributed task queueing try RedisLabs, AWS
ElastiCache is a little difficult to configure. For local redis deployment:

        $ sudo apt-get install redis-server

7. Edit `app/settings/<SETTING>.py` to include Redis server URL by editing the
following line. Set `<REDIS_IP_ADDRESS>` to `127.0.0.1` for local redis.

        ...
        BROKER_URL = "redis://<REDIS_IP_ADDRESS>//"
        ...

8. Update `app/settings/<SETTING>.py` to match current Microbiome DB service

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

9. Copy the 10k files into the `staticfiles/data` directory

10. Run `python manage.py collectstatic` to move the static files to a preset
location

### Optional settings for production
1. Edit the `uwsgi.ini` file to configure logging and development/production
server details (optional)

#### Using `nginx`
1. Install nginx

        $ sudo apt-get install nginx

2. Copy the nginx configuration into `sites-available` and link to
`sites-enabled`

        $ sudo cp vzb_nginx.conf /etc/nginx/sites-available/
        $ sudo ln -s /etc/nginx/sites-available/vzb_nginx.conf /etc/nginx/sites-enabled/
        $ sudo service nginx restart

3. Test by checking if the static files are being served. If not check sockets
to make sure the file has the right permissions or the socket port is not
in use

        http://<SERVER_IP_ADDRESS>:8000/static/css/style.css

## Running a local server
1. Start worker

        $ celery -A darp worker

2. Start `local` server

        $ python manage.py runserver 0.0.0.0:8000

3. Hope for the best 😎

## Running a development or production server
14. Start `development` or `production` server

        $ uwsgi --ini uwsgi.ini

14. Hope for the best 😎

## Stopping servers
- Local servers: `Ctrl-C` in the window where `python manage.py runserver` was
called
- Development or production server:

      $ uwsgi --stop /tmp/vzb-master.pid
