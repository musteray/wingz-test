# Wingz - Project Exercise 👋

This repo is a RESTful API using Django REST Framework for managing ride information.

## System requirements

1. Docker 28.4.0
2. Python 3.12.2

## Setup

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

## Count of trips took > 1 hr from pickup to dropoff

1. Raw SQL
   ```sql
   SELECT 
      DATE_TRUNC('month', pickup_event.created_at) AS ride_month,
      EXTRACT(YEAR FROM pickup_event.created_at) AS year,
      EXTRACT(MONTH FROM pickup_event.created_at) AS month,
      r.id_driver,
      u.first_name || ' ' || u.last_name AS driver_name,
      u.email AS driver_email,
      COUNT(DISTINCT r.id_ride) AS long_rides_count
   FROM 
      ride r
   INNER JOIN 
      "user" u ON r.id_driver = u.id_user
   INNER JOIN 
      ride_event pickup_event ON r.id_ride = pickup_event.id_ride 
      AND pickup_event.description ILIKE '%pickup%'
   INNER JOIN 
      ride_event dropoff_event ON r.id_ride = dropoff_event.id_ride 
      AND dropoff_event.description ILIKE '%dropoff%'
   WHERE 
      -- Calculate duration and filter for rides > 1 hour
      EXTRACT(EPOCH FROM (dropoff_event.created_at - pickup_event.created_at)) > 3600
      -- Ensure pickup happened before dropoff
      AND pickup_event.created_at < dropoff_event.created_at
      -- Only include completed rides
      AND r.status = 'dropoff'
   GROUP BY 
      DATE_TRUNC('month', pickup_event.created_at),
      EXTRACT(YEAR FROM pickup_event.created_at),
      EXTRACT(MONTH FROM pickup_event.created_at),
      r.id_driver,
      u.first_name,
      u.last_name,
      u.email
   ORDER BY 
      ride_month DESC,
      long_rides_count DESC;
   ```

## Referrences

1. [Django, Docker, and PostgreSQL Tutorial](https://learndjango.com/tutorials/django-docker-and-postgresql-tutorial)
2. ...