# Django Ticket Management

A Django ticket management application with user registration, role groups, ticket assignment, Redis-backed WebSocket notifications, and optional Celery background tasks.

## Technology stack

| Technology | Role in this project |
| --- | --- |
| Python 3.9 | Runtime for the Django application and its background worker. |
| Django 3.2.25 | Web framework, templates, authentication, ORM, migrations, and admin. |
| PostgreSQL | Persistent application database, configured as `userdb` in local settings. |
| Redis | Channel layer for real-time notifications and broker/backend services used by Celery. |
| Django Channels 2.2 / channels-redis | WebSocket handling and Redis-backed channel messaging. |
| Daphne 2.3 | ASGI server component used by the Channels stack. |
| Celery 4.3 | Runs asynchronous/background tasks outside web requests. |
| Django REST Framework 3.12 | REST serialization and API support. |
| HTML and CSS | Django templates and static styles for the user interface. |

The exact Python package versions are listed in `TicketProject/requirements.txt`.

## Requirements

- Python 3.9
- PostgreSQL
- Redis

The development settings in `TicketProject/TicketProject/settings/local.py` expect a PostgreSQL database called `userdb`, a role called `admin` with password `password`, and Redis on `localhost:6379`. Update that settings file if your local credentials or service addresses differ.

## Setup on macOS

Install and start PostgreSQL and Redis with Homebrew:

```bash
brew install postgresql redis
brew services start postgresql
brew services start redis
```

Create the database role and database expected by the local settings:

```bash
psql postgres -c "CREATE ROLE admin WITH LOGIN PASSWORD 'password';"
createdb -O admin userdb
```

Create and activate a virtual environment, then install the dependencies:

```bash
cd TicketProject
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install "pip==24.0" "setuptools<58" wheel
pip install --no-build-isolation -r requirements.txt
```

The pip and setuptools versions above are needed because this project includes legacy packages whose package metadata/build scripts are incompatible with current installers.

## Initialize and run

Apply the migrations. The existing migrations create the tables and the `super_admin`, `senior_system_admin`, and `system_admin` groups:

```bash
python manage.py migrate --settings=TicketProject.settings.local
```

Start the development server:

```bash
python manage.py runserver --settings=TicketProject.settings.local
```

Open <http://127.0.0.1:8000/>. Register the first user at <http://127.0.0.1:8000/register/> and select the `super admin` designation, then sign in at <http://127.0.0.1:8000/login/>.

Redis must be running for Channels notifications and Celery. The home view queues a Celery task, so keep a worker running in a second terminal while using the app. Activate the same virtual environment there and run:

```bash
cd TicketProject
source .venv/bin/activate
celery -A TicketProject worker --loglevel=info
```

## Notes

- Run management commands from the `TicketProject` directory and pass `--settings=TicketProject.settings.local` so Django uses the custom user model and PostgreSQL configuration.
- These settings and dependency versions are for local development. The project contains hard-coded development credentials and an old Django release; do not deploy it as-is.
