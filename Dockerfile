FROM python:3.11-slim

WORKDIR /app

ENV DJANGO_SETTINGS_MODULE=djilab.settings
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

COPY 192.168.0.107+2.pem /app/192.168.0.107+2.pem
COPY 192.168.0.107+2-key.pem /app/192.168.0.107+2-key.pem

EXPOSE 8000

CMD ["python", "run_https.py"]
