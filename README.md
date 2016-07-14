# Visibiome: Microbiome Search and Visualization Tool #

## Install ##
Clone this repository:

    $ git clone https://syaffers@bitbucket.org/syaffers/visibiome.git
    $ cd visibiome

Install `virtualenv` for Python (if it doesn't already exist):

    $ sudo pip install virtualenv

Setup virtual environment:

    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements

Migrate and populate database:

    $ python manage.py migrate
    $ python manage.py loaddata data/ecosystem_choices.json

Start worker:

    $ celery -A darp worker

http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html