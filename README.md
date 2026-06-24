# Fitness Club Membership Service

An online membership management and business process automation system for a local fitness club. This project replaces manual spreadsheet tracking and cash payments with a fully automated solution. Members can register, purchase, renew, freeze, resume, or cancel memberships online with secure payments powered by Stripe. Club staff receive instant Telegram notifications for all critical business events.

The project is implemented as a fully functional REST API with interactive, built-in documentation (Swagger/Redoc).

---

## 🚀 Tech Stack

* **Backend:** Python 3.11+, Django 6.0+, Django REST Framework (DRF)
* **Authentication:** JWT (via `djangorestframework-simplejwt`)
* **Database:** PostgreSQL
* **Task Queue & Async Tasks:** Celery + Redis + Celery Beat (for periodic tasks) + Flower (task monitoring)
* **Payments:** Stripe API (Checkout Sessions & Webhooks)
* **Notifications:** Telegram Bot API
* **Code Quality & Tooling:** Docker & Docker-compose, Flake8, Black, Python-decouple
* **API Documentation:** `drf-spectacular` (Swagger UI / Redoc)

---

## 📁 Project Structure (`src/`)

The project follows a modular, domain-driven structure inside the `src` directory:

* `config/` — Main Django project settings, URL routing, and Celery configuration.
* `users/` — User management, custom Member model, registration, and JWT authentication.
* `plans/` — Management of fitness club membership plans (Basic, Standard, Premium).
* `membership/` — Core business logic for memberships: purchasing, renewals, cancellations, and freeze/resume operations.
* `payments/` — Stripe integration, checkout session generation, and webhook processing.
* `notifications/` — Telegram notification module for club staff.

---

## ⚙️ System Specifications & Non-Functional Requirements

* **Concurrency:** Supports up to 5 concurrent users.
* **Capacity:** Scalable up to 1,000 active users.
* **Throughput:** Designed to process ~50,000 memberships per year.
* **Storage Efficiency:** Optimized database footprint (estimated data growth of ~30 MB/year).

---

## 🛠️ Installation & Setup (Local Development via Docker)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/fitness-club-membership-service.git
cd fitness-club-membership-service
```
### 2. Configure Environment Variables
Create a .env file in the root directory based on the provided sample:

```bash
cp .env.sample .env
```
Open the .env file and populate it with your credentials (Django secret key, Database credentials, Stripe API keys, Telegram Bot Token, Staff Chat ID, etc.).

### 3. Build and Run Containerized Services
The entire application is containerized. Start the database, Django server, Redis, Celery worker, Celery beat, and Flower with a single command:

```bash
docker-compose up --build
```
Once all containers are up and running, the following services will be available:

* **API Service:** http://127.0.0.1:8000/

* **Swagger UI:** http://127.0.0.1:8000/api/docs/

* **Redoc:** http://127.0.0.1:8000/api/redoc/

* **Flower (Celery Dashboard):** http://127.0.0.1:5555/

### 4. Run Migrations and Create a Superuser
Open a new terminal window and execute:

```bash
docker-compose exec web python src/manage.py migrate
docker-compose exec web python src/manage.py createsuperuser
```
## 🔄 Background & Periodic Tasks (Celery)
* Celery Beat is configured to handle automated background tasks to maintain systemic integrity:

* Membership Expiration Check: A daily routine checks for memberships nearing their end date. If auto_renew is enabled, it triggers a renewal payment process; otherwise, it transitions the membership status to EXPIRED.

* Freeze/Resume Management: Automatically updates the membership status to FROZEN on the scheduled freeze start date and reverts it back to ACTIVE once the freeze period concludes.

* Staff Alerts: Generates upcoming expiration logs and dispatches daily status reports via Telegram.

## 💳 Stripe Payments Integration
* When a user purchases a new plan or pays an upgrade fee, the system requests a Stripe Checkout Session.

* The API returns a session_url, redirecting the user to a secure Stripe payment page.

* Upon a successful transaction, Stripe fires a webhook event to our dedicated endpoint (/api/payments/webhook/).

* The application validates the webhook signature, sets the payment status to PAID, activates/updates the membership, and triggers a staff notification.

## ✉️ Telegram Notifications
Club staff are kept up-to-date instantly via automated Telegram alerts whenever the following events occur:

* 💰 New Membership Purchase: Triggered when a member successfully purchases a new membership plan.

* ❄️ Freeze Actions: Instant notification when a membership is frozen, including freeze period details.

* ⚠️ Expiration Warnings: Alerts sent at 7, 3, and 1 day before membership end date to help staff proactively manage retention.

* 🔄 Auto-Renew: Automatic membership renewal notification when a membership expires and auto_renew is enabled.

All notifications run asynchronously via Celery and are delivered to a dedicated Telegram chat using a bot.

## 🧪 Linting & Testing
flake8 and black are utilized to maintain high code quality standards and compliance with PEP 8.

Run the linter:

```bash
docker-compose exec web flake8 src/
```
Run the test suite:
```bash
docker-compose exec web python src/manage.py test src/
```
