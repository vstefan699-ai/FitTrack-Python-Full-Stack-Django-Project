# 🏋️ FitTrack Pro

**A full-stack gym and personal-training management web app built with Python, Django and PostgreSQL.**

FitTrack Pro has two separate experiences. **Trainers** build workout plans from a shared exercise library and assign them to members. **Members** log the workouts they complete and follow their progress on a weight chart.

🔗 **Live demo:** [python-full-stack-django-project-9z.vercel.app](https://python-full-stack-django-project-9z.vercel.app)
📂 **Source code:** [github.com/vstefan699-ai/FitTrack-Python-Full-Stack-Django-Project](https://github.com/vstefan699-ai/FitTrack-Python-Full-Stack-Django-Project)

![My Progress page with weight chart](docs/screenshots/06-my-progress.png)

---

## 📑 Table of Contents

- [Demo Login](#-demo-login)
- [The Problem](#-the-problem)
- [Key Features](#-key-features)
- [Screenshots](#-screenshots)
- [Authentication and Role-Based Access](#-authentication-and-role-based-access)
- [Backend Architecture](#-backend-architecture)
- [Database Structure](#-database-structure)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [PostgreSQL / Neon Setup](#-postgresql--neon-setup)
- [Database Migrations](#-database-migrations)
- [Running Locally](#-running-locally)
- [Automated Tests](#-automated-tests)
- [Deployment](#-deployment-vercel--neon)
- [Planned Improvements](#-planned-improvements)
- [About This Project](#-about-this-project)

---

## 🔑 Demo Login

Try the live demo as a member:

| Role | Username | Password |
|---|---|---|
| Member | `demo_member` | `FitTrackDemo2026!` |

🔒 **The trainer demo login is available on request.** The trainer pages are shown in the [screenshots](#-screenshots).

The demo member follows the plan **"Beginner Strength A/B (Demo)"** and has 8 weeks of workout history (three sessions a week, including one lighter "deload" week), so the progress chart has realistic data to show. The demo data is created and refreshed with the [`seed_demo`](#6-optional-add-the-demo-accounts) command.

---

## 🎯 The Problem

A personal trainer working with several clients usually manages programmes in spreadsheets, notebooks or chat messages. That makes it hard to:

- keep one consistent set of exercises across every client's programme,
- give each client a clear plan with target sets and reps,
- see what a client actually did in each session, and
- show a client measurable progress over time.

FitTrack Pro puts this in one web app. The trainer manages the exercise library and plans in one place, and each member gets their own dashboard with their plan, a simple way to log workouts, and a chart of their progress.

The app is designed around **one trainer (or a small team of trainer accounts) and their members**. All trainers share the same plans, exercise library and member list.

---

## ✨ Key Features

### 👟 For trainers

#### Trainer dashboard
- Summary cards: **total plans**, **total members** and **total workout logs**.
- A list of all workout plans, linking to plan management.

#### Exercise library
- One **shared library** of exercises that every plan picks from. Each exercise has a **name**, **muscle group** (Chest, Back, Legs, Shoulders, Arms or Core) and an optional **description**.
- **Add, edit and delete** exercises. Editing an exercise updates it in every plan that uses it.
- **Duplicate protection:** extra spaces are tidied up, and names that differ only in capital letters (for example "bench press" and "Bench Press") are rejected.
- **Delete protection:** an exercise that is used in a plan or in any member's workout history cannot be deleted. The library table shows how many plans and logs use each exercise.

#### Workout plan builder
- Create a plan with a **name** and **description**, then **tick exercises** from the library and set the target **sets** (1–20), **reps** (1–100) and an optional **order** for each one.
- Validation: at least one exercise must be ticked, and every ticked exercise needs sets and reps.
- **Edit** a plan using the same builder, pre-filled with the current values.
- **Delete** a plan. Members on that plan are left without a plan, but **their workout history is kept**.
- The plans page shows each plan's exercises and how many members are on it.
- The builder asks the trainer to add exercises to the library first if the library is empty.

#### Assigning plans to members
- A **Members page** lists every member account (trainer accounts are excluded).
- The trainer picks a plan from a dropdown next to each member and assigns it. Each member has one assigned plan at a time.

### 🏃 For members

#### Member dashboard
- Shows the member's **assigned plan** as exercise cards with the target sets × reps, plus the number of workouts logged.
- Each card has a **Log This** button that opens the workout form with that exercise already selected.
- Shows a clear "No Program Assigned Yet" message if the trainer hasn't assigned a plan.

#### Workout logging
- Log a workout with the **date**, **exercise**, **sets done**, **reps per set**, **weight used (kg)** and optional **notes**.
- Members can only choose exercises from **their own assigned plan**. This is enforced on the server, not only in the dropdown.
- Server-side validation:
  - no dates in the future, and no dates more than 365 days ago (the date picker also greys these out),
  - weight between 0 kg (bodyweight exercises) and 500 kg,
  - sets 1–20 and reps 1–100.

#### Workout history and progress tracking
- The **My Progress** page shows a **Chart.js line chart** of the **heaviest weight used per day** for one exercise. A dropdown switches between any exercise the member has logged.
- Three stat cards for the selected exercise: **Best Weight**, **Change Since First Session** and **Training Days Logged**.
- A full **workout history table** (date, exercise, muscle group, sets × reps, weight and notes), newest first.
- Members only ever see their own logs.

> Workout logs can be created but not edited or deleted from the member pages. A superuser can manage all records through the Django admin.

### 🌐 General
- **Landing page**, **register**, **login** and **logout**.
- **Responsive layout:** a sidebar on larger screens that becomes a top menu bar below 768px.
- **Custom 404 page** for unknown URLs and unknown record IDs.
- **Django admin** (`/admin/`) for superusers, with useful list columns, filters and search for exercises and workout logs, and a plan's exercises editable inside the plan page.

---

## 📸 Screenshots

| Trainer dashboard | Workout plans and exercise library |
|---|---|
| ![Trainer dashboard](docs/screenshots/07-admin-dashboard.png) | ![Workout plans](docs/screenshots/08-workout-plans.png) |

| Plan builder | Members (assign plans) |
|---|---|
| ![Plan builder](docs/screenshots/09-plan-builder.png) | ![Members](docs/screenshots/10-members.png) |

| Member dashboard | Log a workout |
|---|---|
| ![Member dashboard](docs/screenshots/04-member-dashboard.png) | ![Log a workout](docs/screenshots/05-log-workout.png) |

| Landing page | Login | Register (with validation) |
|---|---|---|
| ![Landing page](docs/screenshots/01-landing.png) | ![Login](docs/screenshots/02-login.png) | ![Register with validation errors](docs/screenshots/03-register-validation.png) |

**On mobile** (the sidebar becomes a top menu bar below 768px):

<p>
  <img src="docs/screenshots/11-mobile-member-dashboard.png" alt="Member dashboard on mobile" width="260">
  &nbsp;
  <img src="docs/screenshots/12-mobile-my-progress.png" alt="My Progress on mobile" width="260">
</p>

---

## 🔐 Authentication and Role-Based Access

FitTrack Pro uses **Django's built-in authentication system** (`django.contrib.auth`) instead of a custom one. It is well tested and handles password hashing, sessions and CSRF protection out of the box.

### Registration and login
- **Register** uses a form based on Django's `UserCreationForm`:
  - passwords are **hashed** before they are stored (never saved as plain text),
  - Django's password validators reject short, common, all-numeric and username-like passwords,
  - email is optional, and usernames are checked **case-insensitively**, so "Newbie" is rejected if "newbie" already exists,
  - errors appear under each field, and the username and email are kept when the form is shown again.
- **Login** uses Django's `AuthenticationForm`, which also refuses deactivated accounts, with a short "Invalid username or password." message.
- After logging in or registering, users go straight to the right dashboard for their role. Logged-in users who open the landing, login or register page are redirected to their dashboard.

### Roles
There is no separate "role" table. The role comes from Django's built-in `is_staff` flag:

| Role | How it is set | What they can do |
|---|---|---|
| **Member** | Anyone who signs up on `/register/` | Member dashboard, log workouts, My Progress |
| **Trainer** | A user with `is_staff = True` (for example, created with `createsuperuser` or set in the Django admin) | Trainer dashboard, exercise library, plan builder, members page |
| **Superuser** | `createsuperuser` | Everything a trainer can do, plus the Django admin |

**Why `is_staff`?** It already exists on every Django user, it can be switched on in the Django admin, and it avoids adding an extra model for a two-role app.

### How access is enforced
- Every protected view uses `@login_required`. Visitors who aren't logged in are redirected to the login page.
- Every view also **checks the role**: a member who opens a trainer URL is sent to the member dashboard, and a trainer who opens a member URL is sent to the trainer dashboard.
- The registration form only reads the username, email and password fields, so **nobody can sign up as a trainer** by adding extra form data.
- Actions that change data (**delete plan**, **delete exercise**, **assign plan**) only accept **POST** requests (`@require_POST`) and are protected by Django's **CSRF** tokens. A plain link can never delete anything.
- Unknown IDs show the **404 page** (`get_object_or_404`) instead of an error. Plans can only be assigned to member accounts, never to trainers.

These rules are covered by the [automated tests](#-automated-tests) in `test_permissions.py` and `test_views.py`.

---

## 🏗️ Backend Architecture

FitTrack Pro is a **server-rendered Django application** that follows Django's Model–View–Template (MVT) pattern. There is no separate frontend framework or API: Django builds every page on the server and sends finished HTML to the browser.

```
Browser ──HTTP──▶ fittrack/urls.py ──▶ core/urls.py ──▶ core/views.py
                                                          │   ▲
                                         core/forms.py ◀──┤   │
                                         (validation)     │   │
                                                          ▼   │
                                         core/models.py ──▶ PostgreSQL (Neon)
                                                          │
                                                          ▼
                                   core/templates/core/*.html ──▶ HTML response
```

| Layer | File(s) | Responsibility |
|---|---|---|
| **URLs** | `fittrack/urls.py`, `core/urls.py` | Map each URL to a view and register the custom 404 handler |
| **Views** | `core/views.py` | Function-based views: check the user's role, load data, process forms, choose a template |
| **Forms** | `core/forms.py` | All input validation (register, login, workout log, exercise, plan builder) |
| **Models** | `core/models.py` | Database tables, relationships, delete rules and the profile signal |
| **Templates** | `core/templates/core/` | Pages built from a shared `base.html`, with separate trainer and member sidebar partials |
| **Management command** | `core/management/commands/seed_demo.py` | Creates and refreshes the demo accounts and data |

### Technical decisions explained

| Decision | Why |
|---|---|
| **One Django app (`core`)** | The project is small and its parts are closely linked, so one app keeps things simple. |
| **Validation in Django forms** | Every rule is checked on the server, so it can't be bypassed by editing the page in the browser. The plan builder form builds its tick box, sets, reps and order fields dynamically for every exercise in the library. |
| **Atomic plan saves** (`transaction.atomic`) | A plan and its list of exercises are saved together or not at all, so a failure can never leave a half-saved plan. |
| **"Clear and rebuild" when editing a plan** | Editing deletes the plan's old exercise rows and creates the new ones with `bulk_create`. This is simple and safe, because workout logs point at the exercise, not at the plan. |
| **Efficient queries** | `select_related` and `prefetch_related` load related rows in as few queries as possible, and counts (members per plan, plans and logs per exercise) are calculated in the database with `annotate`. |
| **Chart data grouped in the database** | My Progress uses `values()` + `annotate(Max(...))` so PostgreSQL returns one row per day with the heaviest weight, instead of Python looping over every log. |
| **Automatic user profiles** | A `post_save` signal creates a `UserProfile` for every new user, so every member has somewhere to store their assigned plan. |
| **South African time zone** | `TIME_ZONE = 'Africa/Johannesburg'`, so "today" (for default dates and the future-date check) changes at local midnight. |
| **Chart.js from a CDN** | The chart is drawn in the browser from data the view passes into the template. No JavaScript build step is needed. |

---

## 🗄️ Database Structure

All tables are defined as Django models in `core/models.py`. Users come from Django's built-in `User` model.

| Model | Purpose | Key fields |
|---|---|---|
| `User` (Django built-in) | Accounts for trainers and members | `username`, `email`, `password` (hashed), `is_staff` |
| `UserProfile` | Extra information for each user | `user` (one-to-one), `assigned_plan` |
| `Exercise` | One exercise in the shared library | `name` (unique), `muscle_group`, `description` |
| `WorkoutPlan` | A plan created by a trainer | `name`, `description`, `created_by`, `created_at` |
| `PlanExercise` | One exercise inside one plan, with its targets | `plan`, `exercise`, `sets`, `reps`, `order` |
| `WorkoutLog` | One exercise a member completed | `user`, `exercise`, `completed_on`, `sets_done`, `reps_done`, `weight_used`, `notes` |

### Relationships

```
                 created_by
     User ◀──────────────────── WorkoutPlan
      │  ▲                          │  ▲
      │  │ user (1:1)               │  │ assigned_plan
      │  └──── UserProfile ─────────┘──┘
      │                             │
      │ user                        │ plan
      ▼                             ▼
  WorkoutLog ──exercise──▶ Exercise ◀──exercise── PlanExercise
```

- `PlanExercise` is the **link table** between plans and exercises. It turns a many-to-many relationship into a model that can also store the plan-specific targets (sets, reps, order). The same exercise can appear in many plans with different targets.
- A **unique constraint** stops the same exercise being added to one plan twice.
- **Target versus actual:** the plan stores the *target* sets and reps, while each `WorkoutLog` stores what the member *actually* did.

### Delete rules

| When this is deleted… | …this happens | Rule |
|---|---|---|
| A `WorkoutPlan` | Its `PlanExercise` rows are deleted; members on the plan get "no plan"; **workout logs are kept** | `CASCADE` / `SET_NULL` |
| An `Exercise` | **Blocked** while any plan or workout log uses it | `PROTECT` |
| A `User` | Their profile, workout logs and created plans are deleted | `CASCADE` |

Workout logs point at `Exercise` rather than at the plan. This is a deliberate choice: a member's history survives even if their plan is changed or deleted.

### Migrations history
The `core/migrations/` folder includes two **data migrations** written by hand:
- `0004_copy_targets_to_logs`: filled in the new `sets_done` and `reps_done` fields on existing logs when they were added.
- `0007_build_exercise_library`: converted the old per-plan exercises into the shared exercise library, merging near-duplicate names.

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Language (Vercel runs Python 3.12) |
| Django | 6.0.4 | Web framework: ORM, auth, forms, templates, admin |
| psycopg2-binary | 2.9.12 | PostgreSQL database driver |
| dj-database-url | 3.1.2 | Turns the `DATABASE_URL` string into Django database settings |
| python-dotenv | 1.2.2 | Loads environment variables from a `.env` file |
| WhiteNoise | 6.12.0 | Serves static files (such as the Django admin's CSS) |
| tzdata | 2026.1 | Time zone data for `Africa/Johannesburg` |

### Database
| Technology | Purpose |
|---|---|
| PostgreSQL on [Neon](https://neon.tech) | Production and development database (serverless Postgres with branches) |
| SQLite | Automatic fallback when no `DATABASE_URL` is set, and the database used for tests |

### Frontend
| Technology | Purpose |
|---|---|
| Django templates | Server-rendered HTML pages |
| Bootstrap 5.3 (CDN) | Layout, components and responsive grid |
| Font Awesome 6.4 (CDN) | Icons |
| Chart.js 4.4.1 (CDN) | Progress line chart |
| Custom CSS | Dark theme and mobile menu (in `base.html`) |

### Testing, deployment and tools
| Technology | Purpose |
|---|---|
| Django test framework (`django.test.TestCase`, built on `unittest`) | Automated tests |
| [Vercel](https://vercel.com) | Hosting (Python serverless function) |
| Git and GitHub | Version control |

---

## 📁 Project Structure

```
FitTrack-Python-Full-Stack-Django-Project/
├── core/                              # The main Django app
│   ├── management/commands/
│   │   └── seed_demo.py               # Creates/refreshes the demo accounts and data
│   ├── migrations/                    # Database migrations (0001–0008)
│   ├── templates/
│   │   ├── 404.html                   # Custom "page not found" page
│   │   └── core/                      # All pages, plus partials/ (trainer + member sidebars)
│   ├── tests/
│   │   ├── factories.py               # Helpers that create test users, plans, exercises
│   │   ├── test_models.py
│   │   ├── test_forms.py
│   │   ├── test_views.py
│   │   ├── test_permissions.py
│   │   └── test_seed_demo.py
│   ├── admin.py                       # Django admin configuration
│   ├── forms.py                       # All forms and validation
│   ├── models.py                      # Database models
│   ├── urls.py                        # App URLs
│   └── views.py                       # All views
├── fittrack/                          # Project settings package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py                        # Entry point used by Vercel
├── docs/screenshots/                  # Images used in this README
├── manage.py
├── requirements.txt
└── vercel.json                        # Vercel deployment configuration
```

### Pages

| URL | Page | Who |
|---|---|---|
| `/` | Redirects to the landing page | Everyone |
| `/home/` | Landing page | Visitors (logged-in users go to their dashboard) |
| `/register/` | Create a member account | Visitors |
| `/login/` · `/logout/` | Log in · Log out | Everyone |
| `/admin-dashboard/` | Trainer dashboard | Trainers |
| `/manage-plans/` | Workout plans + exercise library | Trainers |
| `/manage-plans/new/` · `/manage-plans/<id>/edit/` | Plan builder (new · edit) | Trainers |
| `/manage-plans/exercises/new/` · `/manage-plans/exercises/<id>/edit/` | Add · edit an exercise | Trainers |
| `/manage-users/` | Members + assign a plan | Trainers |
| `/user-dashboard/` | Member dashboard | Members |
| `/log-workout/` | Log a workout | Members |
| `/my-progress/` | Progress chart + workout history | Members |
| `/admin/` | Django admin | Superusers |

Delete and assign actions (`/manage-plans/<id>/delete/`, `/manage-plans/exercises/<id>/delete/`, `/assign-plan/<id>/`) are POST-only and are triggered by buttons on the trainer pages.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12 or newer** (required by Django 6)
- **Git**
- *(Optional)* a free **[Neon](https://neon.tech)** account if you want to use PostgreSQL locally. Without one, the app uses SQLite automatically.

### 1. Clone the repository
```bash
git clone https://github.com/vstefan699-ai/FitTrack-Python-Full-Stack-Django-Project.git
cd FitTrack-Python-Full-Stack-Django-Project
```

### 2. Create and activate a virtual environment
A virtual environment keeps this project's packages separate from other Python projects on your computer.

```bash
python -m venv venv
```

```bash
# Windows (PowerShell)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install the dependencies
```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file
See [Environment Variables](#-environment-variables) below.

### 5. Create the database tables
```bash
python manage.py migrate
```

### 6. (Optional) Add the demo accounts
```bash
python manage.py seed_demo
```
This creates a demo trainer (`demo_trainer`), a demo member (`demo_member` / `FitTrackDemo2026!`), six exercises, the plan "Beginner Strength A/B (Demo)" and 8 weeks of workout logs (96 logs). The command prints both logins in the terminal when it finishes.

- It is **safe to run again**: it refreshes the demo data and never creates duplicates.
- It **never touches real accounts**. If a real user has already registered with a demo username, the command stops with an error instead.
- The demo accounts are never superusers.

### 7. (Optional) Create your own trainer account
```bash
python manage.py createsuperuser
```
Superusers are also staff, so this account gets the trainer pages **and** the Django admin.

---

## 🔧 Environment Variables

Settings are read from environment variables. Locally they come from a `.env` file, loaded with `python-dotenv`.

| Variable | Required? | Purpose |
|---|---|---|
| `SECRET_KEY` | **Yes** (except when running tests) | Django's secret key, used for signing sessions and CSRF tokens |
| `DEBUG` | No | `True` shows detailed error pages. Anything else (or not set) means `False` |
| `DATABASE_URL` | No | PostgreSQL connection string. If not set, a local SQLite file (`db.sqlite3`) is used |
| `DEMO_TRAINER_PASSWORD` | No (used by `seed_demo` only) | Private password for `demo_trainer`. If not set, a local-only fallback password is used and a warning is printed. **Always set it when seeding production.** It must be at least 12 characters and must not match the public demo passwords |

Create a file called **`.env`** in the **project root** (the same folder as `manage.py`).

> ⚠️ **Replace the placeholder values** below with your own: generate a new secret key, and paste your own Neon connection string if you use one.

```env
SECRET_KEY=paste-a-long-random-string-here
DEBUG=True

# Optional - leave it out to use SQLite instead
# DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> 🔒 `.env` is already listed in `.gitignore`. **Never commit it.** It contains your secret key and database password.

---

## 🐘 PostgreSQL / Neon Setup

The live app uses **PostgreSQL hosted on [Neon](https://neon.tech)**, a serverless Postgres service. Neon's **branches** work like Git branches for a database. A branch is an instant copy of the data that can be changed without affecting the original.

This project uses:

| Neon branch | Used by |
|---|---|
| `production` | The live site on Vercel |
| `dev` | Local development, so testing never touches real data |

To use Neon for local development:

1. Create a free account at [neon.tech](https://neon.tech) and create a new **project**.
2. *(Recommended)* Create a **`dev` branch** from the main branch, so local work stays separate from production data.
3. In the Neon dashboard, click **Connect**, choose your branch, and copy the **connection string**. It looks like `postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require`.
4. Paste it as `DATABASE_URL` in your `.env` file.
5. Run the [migrations](#-database-migrations) to create the tables in that branch.

`dj-database-url` reads that single string and fills in Django's database settings (engine, host, user, password, database name and SSL mode), so no database details are hard-coded in `settings.py`.

---

## 🧱 Database Migrations

Django migrations are version-controlled instructions that create and update the database tables to match `models.py`. All migrations are already in `core/migrations/`.

```bash
# Create or update the tables in the database DATABASE_URL points to (or SQLite)
python manage.py migrate

# See which migrations have been applied
python manage.py showmigrations core

# After changing models.py: create a new migration file
python manage.py makemigrations
```

> Migrations run against whichever database `DATABASE_URL` points to. Check your `.env` before running them. See [Deployment](#-deployment-vercel--neon) for how production is migrated safely.

---

## 💻 Running Locally

With the virtual environment active, from the project root:

```bash
python manage.py runserver
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**. You can then:
- log in as `demo_member` / `FitTrackDemo2026!` (after running `seed_demo`),
- log in as `demo_trainer` with the password printed by `seed_demo`, or with your own superuser,
- or register a new member account on the **Register** page.

Stop the server with **Ctrl + C**.

---

## 🧪 Automated Tests

The project has **101 automated tests**, written with **Django's built-in test framework** (`django.test.TestCase`, which builds on Python's `unittest`). No extra testing packages are needed.

### Running the tests
From the project root, with the virtual environment active:

```bash
# Run all tests
python manage.py test core

# Show the name of every test as it runs
python manage.py test core -v 2

# Run one test file
python manage.py test core.tests.test_permissions
```

Expected result:
```
Ran 101 tests in ...s

OK
```

### What is tested

| File | Tests | What it covers |
|---|---|---|
| `test_views.py` | 51 | Login, logout and register flows; landing redirects; both dashboards; logging workouts; My Progress chart data; creating, editing and deleting plans and exercises; assigning plans |
| `test_forms.py` | 20 | Validation rules: workout dates, weight limits, sets, plan-only exercises, exercise name tidying and duplicates, plan builder rules and exercise ordering |
| `test_models.py` | 12 | Automatic profiles, the unique exercise-per-plan constraint, exercise delete protection (`PROTECT`), deleting a plan keeps member history, default log date |
| `test_seed_demo.py` | 10 | Demo data command: safe to re-run, never touches real accounts, password rules for `DEMO_TRAINER_PASSWORD` |
| `test_permissions.py` | 8 | Role-based access: visitors sent to login, members blocked from trainer pages and actions, trainers kept out of member pages |

Test data is created with small helper functions in `core/tests/factories.py`.

### How the tests are kept safe and fast
- **Tests always use a throwaway in-memory SQLite database**, even if `DATABASE_URL` points to a real database. `settings.py` detects the `test` command and overrides the database setting, so tests can never change real data.
- A **fast password hasher** is used during tests only, because real password hashing is deliberately slow.
- **No `.env` file is needed**: a test-only secret key is used when `SECRET_KEY` is not set.

---

## ☁️ Deployment (Vercel + Neon)

The live app runs on **Vercel**, with the database on **Neon PostgreSQL**.

### How it is configured
- `vercel.json` uses the `@vercel/python` builder (Python 3.12) to run `fittrack/wsgi.py` as a **serverless function**, and sends every request to it.
- **Static files:** because `vercel.json` uses `builds`, Vercel does not run a build script, so `collectstatic` never runs. Static files still work because WhiteNoise serves them directly from each app's static folder (`WHITENOISE_USE_FINDERS = True`).
- **Environment variables** are set in **Vercel → Project → Settings → Environment Variables**:
  - `SECRET_KEY`: a production-only secret key,
  - `DATABASE_URL`: the Neon `production` branch connection string,
  - `DEBUG` is **not set**, so it defaults to `False`.

### Deploying changes
Vercel is connected to the GitHub repository, so pushing to the main branch deploys automatically.

### Migrating and seeding production
Vercel does **not** run `migrate`. Database changes are applied from a local machine:

1. In Neon, create a **backup branch** of `production` first, so the data can be restored if something goes wrong.
2. Open a **new** PowerShell terminal in the project folder, activate the virtual environment, and run:
   ```powershell
   $env:DATABASE_URL = Read-Host "Paste the production connection string"
   python manage.py migrate

   # Only when the demo data needs refreshing:
   $env:DEMO_TRAINER_PASSWORD = Read-Host "Private demo trainer password"
   python manage.py seed_demo
   ```
3. **Close that terminal** when finished, so the production connection string can't be used by accident later.
4. Push the code changes to GitHub so Vercel deploys them.

`Read-Host` keeps the connection string and password out of files and out of the saved command history. Get the production connection string from **Neon** (project → **Connect** → branch `production`), because Vercel hides the stored value.

---

## 🔮 Planned Improvements

> 🛠️ Everything in this section is **planned and not built yet**.

### Features

#### For trainers
- 📊 **View each member's progress:** let the trainer open any member's workout history and progress chart inside the app. At the moment this data is only visible to the member, or through the Django admin.
- 💬 **Trainer feedback on workouts:** let the trainer leave a short comment on a member's logged workout, for example *"Good form, add 2.5 kg next week"*.
- 🗓️ **Workout days inside a plan:** split a plan into days (for example **Day A** and **Day B**) by adding a day field to `PlanExercise`, so members see which exercises belong to which session.
- 🔒 **Scoped demo trainer:** the demo trainer would only see and edit demo members and plans, so the trainer login can be made public.
- 🚫 **Deactivate members** (`is_active = False`) instead of deleting them, so their workout history is kept.

#### For members
- 📝 **Log a whole session at once:** one form for every exercise in that day's session, instead of logging one exercise at a time.
- ✏️ **Edit and delete workout logs** from the member pages.
- 🏆 **Personal records:** show a *"New PR!"* message when a member beats their best weight for an exercise.
- 📈 **More chart options:** add **estimated one-rep max** (calculated from weight and reps) and **total volume** (sets × reps × weight) as alternatives to the current heaviest-weight chart. Both use data that is already recorded.
- ⚖️ **Bodyweight tracking:** let members log their bodyweight over time, with its own chart.
- 🗓️ **Workout scheduling and reminders.**

#### For everyone
- 🔑 **Forgot password:** reset a password through a link sent by email. This depends on the `ALLOWED_HOSTS` fix under Security below.
- ↩️ **Return to the requested page after login** (`?next=`), with a safe-redirect check.
- 📱 **Progressive Web App (PWA):** installable on phones with a web manifest and service worker.

### Security
- 🛡️ **Restrict `ALLOWED_HOSTS`:** replace the current wildcard (`'*'`) with the real domains (for example `.vercel.app`, `localhost` and `127.0.0.1`). This stops the app from responding to requests that use a fake domain name, and **must** be done before password-reset emails are added.
- ✅ **Production checklist:** work through the warnings from Django's deployment check (`python manage.py check --deploy`).

### Development
- 🤖 **GitHub Actions:** run the test suite automatically on every push.

---

## 📌 About This Project

FitTrack Pro is a **personal portfolio project**, built while studying full-stack web development. It is **not a commercial product** and is not used by a gym or business. The live site exists to demonstrate the app, and the demo accounts contain sample data only.

It demonstrates:
- building a full-stack web application with **Python and Django** (models, views, forms, templates and the admin),
- **relational database design** with PostgreSQL, including link tables, constraints, delete rules and data migrations,
- **authentication and role-based access control**,
- **server-side validation** and safe handling of bad input,
- writing an **automated test suite**,
- deploying to **Vercel** with a cloud **Neon** database and environment-based configuration.

---

## 👤 Author

**Stefan Visser** · [GitHub](https://github.com/vstefan699-ai)