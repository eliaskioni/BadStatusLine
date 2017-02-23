#!/usr/bin/env bash

python manage.py migrate  --noinput --settings=$DJANGO_SETTINGS_MODULE


python manage.py initadmin --username=guest --password=guest --settings=$DJANGO_SETTINGS_MODULE


exec gunicorn --bind=0.0.0.0:80 BadStatusLine.wsgi \
        --workers=5\
        --log-level=info \
        --log-file=-\
        --access-logfile=-\
        --error-logfile=-\
        --timeout 30\
        --reload