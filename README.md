# Visibiome: Microbiome Search and Visualization Tool #

## Install ##
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

6. Setup a Redis cache (try RedisLabs, AWS ElastiCache is a little diffifcult to configure)

7. Edit `app/settings.py` to include Redis server URL by editing the following line

        ...
        BROKER_URL = "redis://<REDIS_IP_ADDRESS>//"
        ...

8. Update `app/betadiversity_scripts/config.py` to match current microbiome DB service

        server_db = dict(
            # assuming you kept the name of the DB as ServerMicroBiome
            db="ServerMicroBiome",
            host="<mysql_server_ip_or_url>",
            user="<server_userame>",
            passwd="<server_password>",
        )

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

12. Start worker

        $ celery -A darp worker

13. Start (development) server

        $ python manage.py runserver 0.0.0.0:8000

14. Hope for the best 😎

## TODO List ##
* http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html
* WSGI integration using Apache backend or something

