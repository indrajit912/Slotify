# 🎛️ Slotify

**Slotify** is a Flask-based web application that digitizes washing machine slot booking in institute hostels. Instead of writing names on a printed chart, students can register, log in, and book available time slots for any washing machine in their hostel — all online!

---
## 👤 Author

**[Indrajit Ghosh](https://indrajitghosh.onrender.com/)** <br>
PhD Scholar, Indian Statistical Institute Bangalore <br>
🧠 Area: Operator Algebras | 🧺 Hobby Project: Slotify

---


## ✨ Features

- 📅 Monthly slot view for each washing machine
- 🔐 Secure registration with institute email
- ✅ Only registered users can book or cancel slots
- 👥 Role-based access: user, admin, superadmin
- 🧼 Configurable daily time slots (e.g., 07:00–10:30)
- 🛠️ Admin dashboard (planned)
- 🔒 Session-based authentication with Flask-Login

---

## 🧱 Tech Stack

- Backend: [Flask](https://flask.palletsprojects.com/)
- ORM: [SQLAlchemy](https://docs.sqlalchemy.org/)
- Forms: [Flask-WTF](https://flask-wtf.readthedocs.io/)
- Auth: [Flask-Login](https://flask-login.readthedocs.io/)
- DB: SQLite (dev) — can be upgraded to PostgreSQL/MySQL
- Logging: Python built-in `logging` module


---

## ⚙️ Local Setup Instructions

### 🔧 1. Clone the Repository

```bash
git clone https://github.com/indrajit912/Slotify.git
cd Slotify
```
### 🐍 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
### 📦 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 🔐 4. Set the Environment Variables in `.flaskenv`
```
FLASK_APP=slotify.py
FLASK_ENV=development
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=8080
FLASK_DEBUG = 1
```

### 🗃️ 5. Initialize the Database
```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

### ▶️ 6. Run the Developement Server
```bash
flask run
```
---

## 📌 Todo

- Admin panel to view all bookings

- Email verification and password reset

- Exportable PDF booking calendar

- Notifications/reminders

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork this repo
2. Create a new branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -m 'Add new feature'`
3. Push to the branch: `git push origin feature-name`
4. Open a pull request
---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.