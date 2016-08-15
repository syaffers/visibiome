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

5. Setup a Redis cache (try RedisLabs, AWS ElastiCache is a little diffifcult to configure)

6. Edit `app/settings.py` to include Redis server URL by editing the following line

        ...
        BROKER_URL = "redis://<REDIS_IP_ADDRESS>//"
        ...

7. Update `app/betadiversity_scripts/config.py` to match current microbiome DB service

        server_db = dict(
            # assuming you kept the name of the DB as ServerMicroBiome
            db="ServerMicroBiome",
            host="<mysql_server_ip_or_url>",
            user="<server_userame>",
            passwd="<server_password>",
        )

8. Set public directories by editing the `MEDIA_ROOT` and `LARGE_DATA_PATH`

       ...
       MEDIA_ROOT = '/path/to/user/writable/directory/media'
       ...
       LARGE_DATA_PATH = '/path/to/user/writable/directory/data'
       ...

8. Make two folders in the public path

7. Start worker

        $ celery -A darp worker
    
## TODO List ##
* http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html
* WSGI integration using Apache backend or something

