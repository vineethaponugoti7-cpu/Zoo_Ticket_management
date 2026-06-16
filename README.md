# Zoo Ticket Management System

A full-stack web application for managing zoo ticket bookings, built with **Flask** and **MongoDB**. It supports two roles — an administrator who manages stalls, activities, and tickets, and customers who register, book and cancel tickets, and pay online.

## Overview

The application models a real ticketing workflow end to end: an admin sets up activities, stalls, and ticket types with tiered pricing, while customers register, log in, book entry and stall tickets for different visitor categories, pay, and request refunds. It was built as a master's project and then cleaned up into a reproducible repository.

| | |
|---|---|
| **Backend** | Python, Flask |
| **Database** | MongoDB (via PyMongo) |
| **Frontend** | HTML templates (Jinja2) + Bootstrap, custom CSS |
| **Auth** | Session-based login for admin and customers, hashed passwords |

## Features

- **Two roles** — separate admin and customer areas, protected by session login.
- **Admin** — add activities, create stalls (with image upload), define ticket types, set tiered prices (adults, children, senior citizens, differently-abled), and view customers, bookings, and payments.
- **Customers** — register and log in, browse tickets, book entry and stall tickets for multiple visitor categories, and pay by card.
- **Bookings** — automatic price calculation across visitor categories and live tracking of remaining tickets.
- **Refunds** — customers can cancel a booking, which records a refund and updates booking and payment status.

## Project structure

```
zoo-management/
├── main.py              # Flask application (routes and logic)
├── templates/           # Jinja2 HTML templates
├── static/
│   ├── style.css
│   └── pictures/        # images (seed images + uploaded stall pictures)
├── requirements.txt
└── README.md
```

## Setup

You need Python 3 and a running MongoDB instance.

```bash
git clone https://github.com/YOUR_USERNAME/zoo-management.git
cd zoo-management
pip install -r requirements.txt
```

Make sure MongoDB is running locally (default `mongodb://localhost:27017/`). You can point the app at a different instance with an environment variable:

```bash
export MONGO_URI="mongodb://localhost:27017/"   # optional
export SECRET_KEY="change-me"                    # optional, for sessions
```

Then run:

```bash
python main.py
```

Open `http://localhost:5000` in your browser.

A default admin account is created automatically on first run:

- **Username:** `admin`
- **Password:** `admin`

(The password is stored hashed in the database, not in plain text. Change it after first login in a real deployment.)

## How it works

- **Data model.** MongoDB collections for `admin`, `customer`, `activities`, `stall`, `ticket`, `booking`, `payment`, and `refunds`. Documents reference each other by `ObjectId`.
- **Authentication.** Passwords are hashed with Werkzeug's `generate_password_hash` and verified with `check_password_hash`. Login state is kept in the Flask session along with the user's role.
- **Booking flow.** When a customer books, the app totals the price across visitor categories, stores the booking, decrements remaining tickets, and moves the customer to a payment page. Cancelling a booking writes a refund record and updates the related booking and payment.

## Limitations & future work

This started as an academic project; a few things would need attention before real-world use:

- **Payment is simulated.** Card details are captured but no real payment gateway is integrated, and card data should never be stored as shown here.
- **Input validation is minimal.** Forms assume well-formed input; a production version needs server-side validation and error handling.
- **No automated tests yet.** Adding unit and integration tests would make the project more robust.
- **Access control could be tightened.** Routes rely on session role but would benefit from consistent decorators enforcing permissions.

Planned improvements: add form validation, protect routes with role-based decorators, integrate a sandbox payment gateway, and add a test suite.
