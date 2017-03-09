copy-staticfiles-dev:
	python manage.py collectstatic -i data/ --settings=vzb.settings.development

create-superuser-dev:
	python manage.py createsuperuser --settings=vzb.settings.development

create-superuser-local:
	python manage.py createsuperuser --settings=vzb.settings.local

load-init-data-dev:
	python manage.py loaddata initial.json --settings=vzb.settings.development

load-init-data-local:
	python manage.py loaddata initial.json --settings=vzb.settings.local

migrate-dev:
	python manage.py migrate --settings=vzb.settings.dev

migrate-local:
	python manage.py migrate --settings=vzb.settings.local

# Drop your database first before running this. Use at your own risk!
reset-dev:
	python manage.py collectstatic -i data/ --settings=vzb.settings.development
	python manage.py migrate --settings=vzb.settings.development
	python manage.py loaddata initial.json --settings=vzb.settings.development
	python manage.py createsuperuser --settings=vzb.settings.development

reset-local:
	rm -r local/
	rm db.sqlite3
	python manage.py migrate --settings=vzb.settings.local
	python manage.py loaddata initial.json --settings=vzb.settings.local
	python manage.py createsuperuser --settings=vzb.settings.local
	# a really hard password

restart-dev:
	uwsgi --stop /tmp/vzb-master.pid
	rm logs/vzb.log
	rm logs/uwsgi.log
	rm logs/celery.log
	sleep 4
	uwsgi --ini uwsgi.ini

start-local:
	python manage.py runserver 8001

start-dev:
	uwsgi --ini uwsgi.ini

start-worker-local:
	celery -A vzb worker

stop-dev:
	uwsgi --stop /tmp/vzb-master.pid
