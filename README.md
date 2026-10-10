## Overview

Built with Django and Django REST Framework.

## Requirements

* Python 3.14
* pip

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run database migrations:

```bash
python manage.py migrate
```

## Run locally

```bash
python manage.py runserver
```

## Test

```bash
python manage.py test
```

## API Endpoints

| Method | Endpoint     | Description |
| ------ |--------------|-------------|
| GET    | `/api/test/` | API check   |

## Project Structure

* `config/`: Django project configuration
* `apps/`: Django applications
* `apps/core/`: Core API endpoints and tests

