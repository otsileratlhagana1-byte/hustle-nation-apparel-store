# HUSTLE NATION — Pro E-commerce

Render-ready Flask + SQLite clothing e-commerce starter for Hustle Nation.

## Dashboards
- Owner / Creator: `/owner/login`
  - Full website control
  - Client dashboard lock/unlock
  - Scheduled maintenance windows
  - Product/order/customer management
  - Theme, logo, homepage and store settings
- Client Admin: `/admin/login`
  - Products, sizes, stock, sale prices
  - Orders and PAXI references
  - Homepage/theme/logo controls
  - Store settings

## Default development credentials
Set these as Render environment variables before production:
- OWNER_USERNAME=owner
- OWNER_PASSWORD=change-me
- CLIENT_USERNAME=admin
- CLIENT_PASSWORD=change-me

The app will create the accounts on first start. Change the passwords immediately.

## Run in Pydroid 3
1. Extract the folder.
2. Install: `pip install -r requirements.txt`
3. Run: `python app.py`
4. Open `http://127.0.0.1:5000`

## Render
Build: `pip install -r requirements.txt`
Start: `gunicorn app:app`

SQLite is suitable for testing/small deployments. For a larger production shop, move the database to PostgreSQL and persistent media storage.

## Important
The PAXI workflow stores the customer's chosen PAXI shipping option and allows the admin to enter a PAXI tracking/reference number. It does not claim to be a live PAXI API integration.

© 2024 Hustle Nation. Designed by Otsile Graphics. © 2026.
