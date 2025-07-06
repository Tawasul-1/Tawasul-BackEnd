# Tawasul — Backend

🎯 **Tawasul** is a web application that supports non-verbal children with autism by providing interactive learning and communication cards.

This repository contains the **backend**, built with Django and Django REST Framework, which serves as the API layer for the frontend (built with React).

---

## 🚀 Features

✅ User registration, login, and profiles
✅ CRUD operations for interactive cards
✅ RESTful API endpoints
✅ CORS enabled for React frontend integration

---

## 🛠️ Tech Stack

* Python
* Django
* Django REST Framework
* django-cors-headers
* SQLite (for development)
* React (frontend, in a separate repository)

---

## 📦 Installation & Setup

Follow these steps to download, install, and run the project locally:

---

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Tawasul-1/Tawasul-BackEnd.git
cd Tawasul-BackEnd
```

---

### 2️⃣ Create & activate a virtual environment

On **Linux/Mac**:

```bash
python3 -m venv venv
source venv/bin/activate
```

On **Windows**:

```bash
python -m venv venv
venv\Scripts\activate
```

---

### 3️⃣ Install the dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Apply database migrations

```bash
cd project
python manage.py migrate
```

This will create all the necessary database tables, including the `auth_user` table.

---

### 5️⃣ Create a superuser (optional)

If you want to access the Django admin panel, create a superuser:

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

---

### 6️⃣ Run the development server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) to see the backend running.
