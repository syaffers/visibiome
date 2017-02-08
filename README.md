# Visibiome: Microbiome Search and Visualization Tool #

## Setup ##
There are three possible deployment settings (indicated in this document with a
  placeholder `<SETTING>`). The settings are `local`, `deployment`, `production`
  which is stored under `vzb/settings`. Any lines showing the `$` sign at the
  start are terminal commands while lines that begin with `...` are parts of
  a file.

1. Start a VM or EC2 server with QIIME pre-installed.

2. Clone this repository

        $ git clone https://syaffers@bitbucket.org/syaffers/visibiome.git
        $ cd visibiome

3. Install app dependencies (you may need superuser credentials)

        $ pip install -r requirements.txt

4. Move the static files for live deployment (for `development` and `production`
  settings only, do not perform for `local` setting!)

        $ python manage.py collectstatic --settings=vzb.settings.development

5. Visibiome handles many relational database systems but we use MySQL. Edit
  `vzb/settings/<SETTING>.py` to update the webserver database configuration. Be
  sure to create the database before doing the following steps

        ...
        DATABASES = {
          'default': {
              ...
              'ENGINE': 'django.db.backends.mysql',
              'NAME': 'Visibiome',
              'USER': 'root',
              # Consider placing the password in an environment variable
              'PASSWORD': 'qiime',
              # Or an IP Address that your DB is hosted on
              'HOST': 'localhost',
              'PORT': '3306',
          },
        ...

6. Migrate and populate database. Clear (or delete) the current database to
  start with a fresh installation.

        $ python manage.py migrate --settings=vzb.settings.<SETTING>
        $ python manage.py loaddata data/ecosystem_choices.json --settings=vzb.settings.<SETTING>

7. Create an admin account (optional, but useful!). Change `<SETTING>` to your
  current deployment settings

        $ python manage.py createsuperuser --settings=vzb.settings.<SETTING>

8. Setup a Redis cache. For distributed task queueing try RedisLabs, AWS
  ElastiCache is a little difficult to configure. For local redis deployment:

        $ sudo apt-get install redis-server

9. Edit `vzb/settings/<SETTING>.py` to include Redis server URL by editing the
  following line. Set `<REDIS_IP_ADDRESS>` to `127.0.0.1` for local redis.

        ...
        BROKER_URL = "redis://<REDIS_IP_ADDRESS>//"
        ...

10. Update `vzb/settings/<SETTING>.py` to match current Microbiome DB service

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

11. Download distance matrix files into the `staticfiles/data` directory (for
  local deployment, put into `app/static/data/` folder)

        $ cd staticfiles/ (or app/static/ for local)
        $ mkdir data/
        $ cd data/
        $ wget https://s3.amazonaws.com/visibiome-data-files/10k_bray_curtis_adaptive.npy.gz
        $ wget https://s3.amazonaws.com/visibiome-data-files/10k_samples.pcl
        $ gunzip 10k_bray_curtis_adaptive.npy.gz

### Additional Settings for production
1. Edit the `prjroot` variable in `uwsgi.ini` file to configure paths correctly.
  The `prjroot` value should point to the visibiome folder:

        ...
        prjroot        = /home/ubuntu/visibiome/
        ...

2. Edit the `vzb_nginx.conf` to configure paths correctly in the same manner:

        ...
        alias /home/ubuntu/visibiome/mediafiles;
        ...
        alias /home/ubuntu/visibiome/staticfiles;
        ...
        include          /home/ubuntu/visibiome/uwsgi_params;
        ...

#### Using `nginx`
1. Install nginx

        $ sudo apt-get install nginx

2. Stop any other web servers sub as Apache

        $ sudo service apache2 stop

3. Copy the nginx configuration into `sites-available` and link to
  `sites-enabled`

        $ sudo cp vzb_nginx.conf /etc/nginx/sites-available/
        $ sudo ln -s /etc/nginx/sites-available/vzb_nginx.conf /etc/nginx/sites-enabled/
        $ sudo service nginx restart

4. Test by checking if the static files are being served. If not check sockets
  to make sure the file has the right permissions or the socket port is not
  in use

        http://<SERVER_IP_ADDRESS>:8000/static/css/style.css

5. Add the server IP address into the appropriate settings file you are using
  (e.g. `vzb/settings/development.py`):

        ...
        ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '<SERVER_IP_ADDRESS>']
        ...

#### Automating guest job deletions (optional)
1. Commands have been configured for guest job deletions. By default, jobs
  expire daily although this can be changed by editing the `k` value in
  `app/management/commands/deleteguestjobs.py`. `k = 1` denotes that jobs expire
  daily, `k = 2` denotes that jobs expire every 2 days and so on

        ...
        def handle(self, *args, **options):
              k = 1 # <== change as you see fit
        ...

2. Setup a cron job to run the `delete_jobs.sh` shell command which runs the
  delete guest jobs every hour:

        $ crontab -e

3. Add the following line to the end of the file (changing the visibiome path
  as required):

        0 * * * * bash /home/ubuntu/visibiome/delete_jobs.sh

4. Delete logs can be viewed in `logs/delete.log` (if path is not changed in
  `delete_jobs.sh`).

5. Alternatively, you can manually run the shell script without the need to
  setup a cron job although this is not repeated automatically.


## Running a local server
1. Start worker

        $ celery -A vzb worker

2. Start `local` server

        $ python manage.py runserver 0.0.0.0:8000

3. Check your webserver IP at port 8000 and hope for the best 😎

## Running a development or production server
14. Start `development` or `production` server

        $ uwsgi --ini uwsgi.ini

14. Check your webserver IP at port 8000 and hope for the best 😎

## Stopping servers
- Local servers: `Ctrl-C` in the window where `python manage.py runserver` was
called
- Development or production server:

        $ uwsgi --stop /tmp/vzb-master.pid


Hello, world