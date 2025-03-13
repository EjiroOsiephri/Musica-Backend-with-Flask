FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["sh", "-c", "sleep 5 && gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app"]
