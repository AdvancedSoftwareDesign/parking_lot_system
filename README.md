## Overview

Built with Django and Django REST Framework.

## Requirements

- Python 3.14
- pip

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run database migrations:

```bash
python manage.py migrate
```

### Create a Test Account

Create an admin account:

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username and password.

## Run Locally

```bash
python manage.py runserver
```

## Test

```bash
python manage.py test
```

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/health/` | API health check |
| POST | `/api/login/` | Login and obtain an authentication token |
| GET | `/api/home/` | Access authenticated user homepage |

To log in, send a POST request to `/api/login/` with:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

For protected endpoints, include the returned token in the request header:

```http
Authorization: Token your_token
```

## Project Structure

- `config/`: Django project configuration
- `apps/`: Django applications
- `apps/core/`: Core application
- `apps/core/views/`: API request handlers
- `apps/core/services/`: Business logic
