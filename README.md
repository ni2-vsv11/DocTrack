# 📁 DocTrack – Digital Document Tracking System

DocTrack is a web-based document tracking system developed using **Python and Django**.  
The system helps users upload, manage, and track documents digitally, improving transparency, organization, and efficiency.

This project is developed as an **academic mini project** and follows standard Django development practices.

---

## 🚀 Features

- 📤 Digital document upload and management  
- 📊 Dashboard to track document status  
- 🔄 Real-time document tracking  
- 🔐 User authentication (Login / Logout)
- 🧑‍💼 Admin panel for management
- 🕒 Timestamp-based activity tracking  
- 📁 Proper handling of static & media files  
- 🎨 Clean and modern UI  

---

## 📸 Screenshots

### Home
<img width="1360" height="695" alt="Home-1" src="https://github.com/user-attachments/assets/388e247c-bef4-4497-b8ef-c6831cc763e0" />


### 📊 Dashboard
<img width="1360" height="695" alt="User-Dashboard" src="https://github.com/user-attachments/assets/f06eade8-50ee-44f6-a68c-aa38dd3ada12" />


### 📤 Document Upload
<img width="1360" height="695" alt="Upload-Doc" src="https://github.com/user-attachments/assets/c686ff65-26c5-418e-96e0-2575860e545f" />


### 🧑‍💼 Admin Panel
<img width="1360" height="695" alt="Admin" src="https://github.com/user-attachments/assets/4b1f88c8-06a4-492e-be61-0a91eb00ec85" />


---

## 🛠️ Tech Stack

| Technology | Purpose |
|---


DocTrack/
│
├── doctrack/ # Main Django app
├── doctrack_project/ # Project settings
├── templates/ # HTML templates
├── static/ # CSS, JS, images
├── media/ # Uploaded files
├── attached_assets/ # Supporting assets
├── script/ # Utility scripts
│
├── .venv/ # Virtual environment
├── db.sqlite3 # SQLite database
├── manage.py # Django entry point
├── pyproject.toml # Project configuration
├── uv.lock # Dependency lock file
├── .gitignore


---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

git clone https://github.com/ni2-vsv11/DocTrack.git
cd DocTrack

2️⃣ Create & Activate Virtual Environment
python -m venv .venv
source .venv/bin/activate   # Linux / macOS

3️⃣ Install Dependencies
pip install django

4️⃣ Run Database Migrations
python manage.py makemigrations
python manage.py migrate

5️⃣ Create Superuser
python manage.py createsuperuser

6️⃣ Run Development Server
python manage.py runserver


Open in browser:
http://127.0.0.1:8000/


Admin Panel:
http://127.0.0.1:8000/admin/

🔐 Security Features

Django authentication system

Password hashing

CSRF protection

Role-based access control

Server-side validation

🎯 Use Cases

Academic document tracking

Department-level document monitoring

Office document workflow management

Mini / major project demonstration

🚀 Future Enhancements

Email notifications for document updates

Document version control

Approval workflow system

Advanced search & filters

Cloud storage integration

👨‍💻 Developer

Nitesh Vasave
MCA Student | Software Developer
GitHub: ni2-vsv11

📜 License

This project is developed for educational purposes and is free to use for learning and academic demonstrations.


---

## ✅ Final Checklist Before Pushing to GitHub

```bash
git add README.md screenshots
git commit -m "Add final README with screenshots"
git push
