# Wingz - Project Exercises 👋

This repo is a RESTful API using Django REST Framework for managing ride information.

### System requirements

1. Docker 28.4.0
2. Python 3.12.2

### Setup

1. Clone repo

   ```bash
   git clone git@github.com:musteray/wingz-test.git
   ```

2. Modify docker env file

   ```bash
   1. cp .env.sample .env
   2. Edit .env if want someting to modify
   ```

3. Build docker

   ```bash
   docker compose up -d
   ```

4. Run migration

   ```bash
   docker compose exec web python manage.py migrate
   ```

5. Import `Wingz - Exercise.postman_collection.json` to your Postman for API Ref.

* API URL: http://localhost:9000
* PGAdmin: http://localhost:5050

### Referrences

1. [Django, Docker, and PostgreSQL Tutorial](https://learndjango.com/tutorials/django-docker-and-postgresql-tutorial)
2. ...