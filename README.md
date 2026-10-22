# 🏋️ FitTrack Pro

**FitTrack Pro** is a full-stack gym management web app built with **Django** and **PostgreSQL**. Admins create workout plans, add exercises and assign plans to members. Members log their workouts and track their progress over time.

🔗 **Live demo:** [python-full-stack-django-project-9z.vercel.app](https://python-full-stack-django-project-9z.vercel.app)

<!-- TODO: add screenshots to a /screenshots folder and uncomment the lines below -->
<!--
![Landing page](screenshots/landing.png)
![Admin dashboard](screenshots/admin-dashboard.png)
![User dashboard](screenshots/user-dashboard.png)
-->

---

## ✨ Features

### For admins
- **Admin dashboard** with an overview of the gym
- **Manage workout plans:** create plans with a name and description
- **Add exercises** to each plan, with muscle group (chest, back, legs, shoulders, arms, core), sets, reps and an optional description
- **Manage users** and **assign a workout plan** to each member

### For members
- **Register** an account and **log in / log out**
- **User dashboard** showing the member's assigned workout plan
- **Log workouts:** record the weight used for an exercise, plus optional notes (the date is saved automatically)
- **My progress:** view a history of logged workouts

### Under the hood
- A **user profile is created automatically** for every new user via a Django `post_save` signal, so every account is ready to receive a plan
- Role-based dashboards: admins and members see different pages
- Static files served in production with **WhiteNoise**
- Database connection configured from an environment variable with **dj-database-url**

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 6.0.4 |
| Database | PostgreSQL (hosted on [Neon](https://neon.tech)) |
| DB driver | psycopg2-binary 2.9.12 |
| DB config | dj-database-url 3.1.2 |
| Static files | WhiteNoise 6.12.0 |
| Environment variables | python-dotenv 1.2.2 |
| Hosting | [Vercel](https://vercel.com) |

---

## 🗂️ Data Model

| Model | Purpose | Key fields |
|---|---|---|
| `WorkoutPlan` | A plan created by an admin | `name`, `description`, `created_by` (User), `created_at` |
| `Exercise` | An exercise inside a plan | `workout_plan`, `name`, `muscle_group`, `sets`, `reps`, `description` |
| `WorkoutLog` | A record of a member completing an exercise | `user`, `exercise`, `weight_used`, `completed_on`, `notes` |
| `UserProfile` | Extra info linked one-to-one with each user | `user`, `assigned_plan` |

**Relationships:**

```
User ──< WorkoutPlan ──< Exercise ──< WorkoutLog >── User
 │                ▲
 └── UserProfile ─┘ (assigned_plan)
```

- One plan has many exercises (deleting a plan deletes its exercises)
- One user has many workout logs
- Each user has one profile, which can point to one assigned plan (if the plan is deleted, the assignment is cleared instead of deleting the profile)

---

## 🧭 Pages

| URL | Page | Who uses it |
|---|---|---|
| `/home/` | Landing page | Everyone |
| `/register/` | Create an account | New members |
| `/login/` | Log in | Everyone |
| `/logout/` | Log out | Logged-in users |
| `/admin-dashboard/` | Admin overview | Admins |
| `/manage-plans/` | Create and edit workout plans and exercises | Admins |
| `/manage-users/` | View members | Admins |
| `/assign-plan/<user_id>/` | Assign a plan to a member | Admins |
| `/user-dashboard/` | Member overview and assigned plan | Members |
| `/log-workout/` | Log a completed exercise | Members |
| `/my-progress/` | Workout history | Members |

<!-- TODO: if core/urls.py includes the app under a prefix (e.g. 'fittrack/'), add that prefix to the URLs above -->

---

## 📁 Project Structure

```
Python-Full-Stack-Django-Project/
├── core/              # Project settings package (settings.py, urls.py, wsgi.py)
├── fittrack/          # Main app (models, views, urls, templates)
├── manage.py
├── requirements.txt
├── build_files.sh     # Vercel build script
└── vercel.json        # Vercel deployment config
```

---

## 🚀 Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/vstefan699-ai/Python-Full-Stack-Django-Project.git
cd Python-Full-Stack-Django-Project
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file in the project root
```env
# TODO: confirm these names match what core/settings.py reads
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

> ⚠️ Never commit your `.env` file. Make sure it is listed in `.gitignore`.

### 5. Apply migrations
```bash
python manage.py migrate
```

### 6. Create an admin account
```bash
python manage.py createsuperuser
```

### 7. Start the development server
```bash
python manage.py runserver
```

Then open [http://127.0.0.1:8000/home/](http://127.0.0.1:8000/home/) in your browser.

---

## ☁️ Deployment

The app is deployed on **Vercel**, with the database hosted on **Neon PostgreSQL**.

- `vercel.json` tells Vercel how to build and route the Django app
- `build_files.sh` installs dependencies and collects static files during the build
- WhiteNoise serves the collected static files in production
- Environment variables (`SECRET_KEY`, `DATABASE_URL`, etc.) are set in the Vercel project settings, not in the code

<!-- TODO: confirm build_files.sh steps match the description above -->

---

## 🔮 Future Improvements

- 📱 **Progressive Web App (PWA):** make FitTrack Pro installable on phones with a web manifest and service worker
- 📈 Progress charts showing weight increases per exercise over time
- 🗓️ Workout scheduling and reminders
