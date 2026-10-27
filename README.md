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

| Method | Endpoint | Description | Access |
| ------ | -------- | ----------- | ------ |
| GET | `/api/check/` | Check whether the API is running | Public |
| POST | `/api/login/` | Log in and obtain an authentication token | Public |
| GET | `/api/home/` | Access the authenticated user homepage | Authenticated users |
| POST | `/api/register/` | Register a vehicle for the authenticated user | Authenticated users |
| POST | `/api/parking-lots/` | Create a parking lot | Staff only |
| PATCH | `/api/parking-lots/<parking_lot_id>/capacity/` | Update a parking lot's capacity | Staff only |
| POST | `/api/parking-lots/<parking_lot_id>/subscription/` | Subscribe to parking lot notifications | Authenticated users |
| DELETE | `/api/parking-lots/<parking_lot_id>/subscription/` | Unsubscribe from parking lot notifications | Authenticated users |

### Authentication

To log in, send a `POST` request to `/api/login/`:

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

### Vehicle Registration

Send a `POST` request to `/api/register/`:

```json
{
  "registration_number": "ABC-123"
}
```

The vehicle is registered to the authenticated user.

### Create a Parking Lot

A staff user can send a `POST` request to `/api/parking-lots/`:

```json
{
  "capacity": 100
}
```

The response includes the new parking lot's ID and capacity. Capacity must be an integer of at least `1`.

### Update Parking Lot Capacity

A staff user can send a `PATCH` request to `/api/parking-lots/<parking_lot_id>/capacity/`:

```json
{
  "capacity": 150
}
```

Replace `<parking_lot_id>` with the ID of the parking lot to update. Capacity must be an integer of at least `1`.

### Manage Parking Lot Subscriptions

An authenticated user can subscribe to notifications by sending a `POST` request to:

```http
/api/parking-lots/<parking_lot_id>/subscription/
```

To unsubscribe, send a `DELETE` request to the same endpoint. Neither request requires a JSON body.

The notification feature uses the Observer pattern. The current implementation prints messages to the server console when a parking lot is full or a space becomes available.

## Project Structure

- `config/`: Django project configuration
- `apps/`: Django applications
- `apps/core/`: Core application
- `apps/core/models/`: Database models
- `apps/core/views/`: API request handlers
- `apps/core/services/`: Business logic
- `apps/core/observers/`: Observer classes for parking notifications
- `apps/core/tests/`: Automated tests