web: gunicorn --config deploy/gunicorn.conf.py TheProject.wsgi:application
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
