copy-staticfiles-dev:
	python manage.py collectstatic -i data/ --settings=vzb.settings.development

# Delete your database for this to work properly! Use at your own risk!
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

start-worker-local:
	celery -A vzb worker

start-local:
	python manage.py runserver 8001

start-dev:
	uwsgi --ini uwsgi.ini

stop-dev:
	uwsgi --stop /tmp/vzb-master.pid

restart-dev:
	uwsgi --stop /tmp/vzb-master.pid
	rm logs/vzb.log
	rm logs/uwsgi.log
	rm logs/celery.log
	sleep 4
	uwsgi --ini uwsgi.ini
