# Visibiome: Microbiome Search and Visualization Tool #

## Install ##
1. Start a VM or EC2 server with QIIME pre-installed.

2. Clone this repository:
```
    $ git clone https://syaffers@bitbucket.org/syaffers/visibiome.git
    $ cd visibiome
```
3. Install app dependencies
```
    $ pip install -r requirements.txt
```
4. Migrate and populate database:
```
    $ python manage.py migrate
    $ python manage.py loaddata data/ecosystem_choices.json
```
5. Setup a Redis cache (somehow)

6. Edit `app/settings.py` to include Redis server URL by editing the following line
```
    ...

    BROKER_URL = "redis://<REDIS_IP_ADDRESS>//"

    ...
```
7. Start worker:
```
    $ celery -A darp worker
```
http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html
