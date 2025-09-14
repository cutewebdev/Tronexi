release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn brokerage_backend.wsgi
