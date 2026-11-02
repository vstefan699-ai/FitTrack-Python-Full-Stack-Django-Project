# 🏋️ FitTrack Pro

**FitTrack Pro** is a full-stack gym management web app built with **Django** and **PostgreSQL**.
Trainers build workout plans from a shared exercise library and assign them to members.
Members log their workouts and follow their progress on a weight chart.

🔗 **Live demo:** [python-full-stack-django-project-9z.vercel.app](https://python-full-stack-django-project-9z.vercel.app)

![My Progress page with weight chart](docs/screenshots/06-my-progress.png)

---

## 🔑 Demo logins

Try the live demo as a member:

| Role | Username | Password |
|---|---|---|
| Member | `demo_member` | `FitTrackDemo2026!` |

🔒 **Trainer demo login available on request.** The trainer pages are shown in the screenshots below.

The demo member has 8 weeks of workout history on the plan **"Beginner Strength A/B (Demo)"**, including a deload week, so the progress chart has something real to show.
The demo data is reset regularly with the `seed_demo` command (see below).

---

## 📸 Screenshots

| Admin dashboard | Workout Plans |
|---|---|
| ![Admin dashboard](docs/screenshots/07-admin-dashboard.png) | ![Workout Plans](docs/screenshots/08-workout-plans.png) |

| Plan builder | Members |
|---|---|
| ![Plan builder](docs/screenshots/09-plan-builder.png) | ![Members](docs/screenshots/10-members.png) |

| Member dashboard | Log a workout |
|---|---|
| ![Member dashboard](docs/screenshots/04-member-dashboard.png) | ![Log a workout](docs/screenshots/05-log-workout.png) |

| Landing page | Login | Register (with validation) |
|---|---|---|
| ![Landing page](docs/screenshots/01-landing.png) | ![Login](docs/screenshots/02-login.png) | ![Register with validation errors](docs/screenshots/03-register-validation.png) |

**On mobile** (the sidebar turns into a top menu bar under 768px):

<p>
  <img src="docs/screenshots/11-mobile-member-dashboard.png" alt="Member dashboard on mobile" width="260">
  &nbsp;
  <img src="docs/screenshots/12-mobile-my-progress.png" alt="My Progress on mobile" width="260">
</p>

---

## ✨ Features

### For trainers
- **Admin dashboard** with the number of plans, members and logged workouts
- **Shared exercise library:** add, edit and delete exercises (name, muscle group, description)
  - Near-duplicate names like "bench press" vs "Bench Press" are blocked
  - An exercise that is used in a plan or in someone's workout history can't be deleted
- **Plan builder:** tick exercises from the library and set sets, reps and the order for each one
- **Edit and delete plans:** deleting a plan never deletes the members' workout history
- **Members page:** see every member and **assign a plan** to each one

### For members
- **Register, log in and log out** with Django's built-in auth forms (password strength rules, clear errors under each field)
- **Member dashboard** with the assigned plan as exercise cards (target sets × reps) and a **Log This** button on each card
- **Log a workout:** date, exercise, sets and reps done, weight and notes
  - Only exercises from the member's own plan can be chosen
  - No dates in the future or more than a year back; weight must be 0–500 kg
- **My Progress:** a Chart.js line chart of the heaviest weight per day for any logged exercise, stat cards (best weight, change since the first session, training days logged) and the full workout history

### Under the hood
- **Role-based access:** trainers are Django staff users (`is_staff`); every view checks the role
- **Safe by default:** delete/assign actions only accept POST requests, unknown ids show a 404 page instead of crashing, and all input is validated on the server
- **Plan saves are atomic** (`transaction.atomic`): a plan and its exercise list are saved together or not at all
- **Efficient queries** with `select_related`, `prefetch_related` and database-side counting (`annotate`)
- A **user profile is created automatically** for every new account via a `post_save` signal
- **Responsive layout** with shared sidebar partials for trainers and members
- **Custom 404 page** and South African time zone (`Africa/Johannesburg`), so "today" flips at local midnight
- **96 automated tests** (models, forms, views, permissions and the seed command)
- **`seed_demo` management command** that creates or refreshes the demo accounts and their data

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 6.0.4 |
| Database | PostgreSQL on [Neon](https://neon.tech) (SQLite locally if no `DATABASE_URL` is set) |
| DB driver / config | psycopg2-binary 2.9.12, dj-database-url 3.1.2 |
| Frontend | Django templates, Bootstrap 5, Font Awesome, Chart.js 4.4.1 |
| Static files | WhiteNoise 6.12.0 |
| Environment variables | python-dotenv 1.2.2 |
| Testing | Django's test framework (`TestCase`) |
| Hosting | [Vercel](https://vercel.com) |

---

## 🗂️ Data model

| Model | Purpose | Key fields |
|---|---|---|
| `Exercise` | One exercise in the shared library | `name`, `muscle_group`, `description` |
| `WorkoutPlan` | A plan made by a trainer | `name`, `description`, `created_by` |
| `PlanExercise` | An exercise inside a plan, with its targets | `plan`, `exercise`, `sets`, `reps`, `order` |
| `WorkoutLog` | One workout a member did | `user`, `exercise`, `completed_on`, `sets_done`, `reps_done`, `weight_used`, `notes` |
| `UserProfile` | Extra info for each user | `user`, `assigned_plan` |

```
WorkoutPlan ──< PlanExercise >── Exercise ──< WorkoutLog >── User
     ▲                                                        │
     └──────────── UserProfile.assigned_plan ─────────────────┘
```

**Delete rules:**
- Deleting a plan removes its `PlanExercise` rows, and members on that plan get "no plan". Their workout logs stay, because logs point at `Exercise`, not at the plan.
- An `Exercise` is protected (`on_delete=PROTECT`) while any plan or workout log still uses it.

---

## 🧭 Pages

| URL | Page | Who |
|---|---|---|
| `/` | Redirects to the landing page | Everyone |
| `/home/` | Landing page | Everyone |
| `/register/` | Create a member account | New members |
| `/login/` | Log in | Everyone |
| `/logout/` | Log out | Logged-in users |
| `/admin-dashboard/` | Admin dashboard | Trainers |
| `/manage-plans/` | Workout Plans + exercise library | Trainers |
| `/manage-plans/new/` | Plan builder (new plan) | Trainers |
| `/manage-plans/<id>/edit/` | Plan builder (edit plan) | Trainers |
| `/manage-plans/exercises/new/` | Add an exercise | Trainers |
| `/manage-plans/exercises/<id>/edit/` | Edit an exercise | Trainers |
| `/manage-users/` | Members + assign a plan | Trainers |
| `/user-dashboard/` | Member dashboard | Members |
| `/log-workout/` | Log a workout | Members |
| `/my-progress/` | Progress chart + history | Members |
| `/admin/` | Django admin | Superusers |

---

## 📁 Project structure

```
FitTrack-Python-Full-Stack-Django-Project/
├── core/                          # The app
│   ├── management/commands/
│   │   └── seed_demo.py           # Demo accounts + data
│   ├── migrations/
│   ├── templates/core/            # Pages + partials/ (sidebars)
│   ├── tests/                     # factories + test files
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── fittrack/                      # Settings package (settings.py, urls.py, wsgi.py)
├── docs/screenshots/              # Images used in this README
├── manage.py
├── requirements.txt
└── vercel.json                    # Vercel deployment config
```

---

## 🚀 Run it locally

### 1. Clone the repository
```bash
git clone https://github.com/vstefan699-ai/FitTrack-Python-Full-Stack-Django-Project.git
cd FitTrack-Python-Full-Stack-Django-Project
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install the dependencies
```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file in the project root (next to `manage.py`)
```env
SECRET_KEY=paste-a-long-random-string-here
DEBUG=True
# Optional: leave DATABASE_URL out to use a local SQLite file (db.sqlite3)
# DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

Generate a secret key with:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> ⚠️ Never commit your `.env` file. Make sure it is listed in `.gitignore`.

### 5. Create the database tables
```bash
python manage.py migrate
```

### 6. Add the demo accounts and data
```bash
python manage.py seed_demo
```
This creates a demo trainer (`demo_trainer`) and a demo member (`demo_member`, password `FitTrackDemo2026!`), a demo plan, 6 exercises and 8 weeks of workout logs.
It is safe to run again: it refreshes the demo data and never touches real accounts.

### 7. Start the server
```bash
python manage.py runserver
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with a demo account.

**Your own trainer account:** run `python manage.py createsuperuser`. Superusers are staff, so they get the trainer pages and the Django admin.

---

## 🧪 Run the tests

```bash
python manage.py test core -v 2
```

- **96 tests** in `core/tests/`: `test_models.py`, `test_forms.py`, `test_views.py`, `test_permissions.py`, `test_seed_demo.py` (test data comes from `factories.py`)
- Tests always run on a **throwaway in-memory SQLite database**, even if `DATABASE_URL` points at a real database
- A fast password hasher is used during tests only, and no `.env` file is needed

---

## ☁️ Deployment (Vercel + Neon)

- **Vercel** runs the app as a Python serverless function. `vercel.json` uses `builds` with `@vercel/python` (Python 3.12) and sends every route to `fittrack/wsgi.py`.
- Because `builds` is used, Vercel runs **no build script**, so `collectstatic` never runs. Static files still work because WhiteNoise serves them straight from each app's static folder (`WHITENOISE_USE_FINDERS = True`).
- **Environment variables** are set in the Vercel project settings: `SECRET_KEY` and `DATABASE_URL`. `DEBUG` is left unset, so it defaults to `False`.
- **Neon** has two database branches: `production` (used by the live site) and `dev` (used for local development).

### Migrations and seeding on production
Vercel doesn't run `migrate`, so production database commands are run from a local machine:

1. In Neon, create a **backup branch** of `production` first.
2. Open a **new** PowerShell terminal in the project folder (with the venv active) and run:
   ```powershell
   $env:DATABASE_URL = Read-Host "Paste the production connection string"
   python manage.py migrate
   python manage.py seed_demo
   ```
3. **Close that terminal** when done, so the production URL can't be used by accident later.

`Read-Host` keeps the connection string out of files and out of the command history.

---

## 🔮 Future ideas

- 🚫 **Deactivate members** (`is_active = False`) instead of deleting them, so their history is kept
- ↩️ **Return to the requested page after login** (`?next=`), with a safe-redirect check
- 🤖 **GitHub Actions** to run the test suite on every push
- 📱 **Progressive Web App (PWA):** installable on phones with a web manifest and service worker
- 🗓️ Workout scheduling and reminders

---

## 👤 Author

**Stefan Visser** · [GitHub](https://github.com/vstefan699-ai)
