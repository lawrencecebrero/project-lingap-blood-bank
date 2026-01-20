**PROJECT LINGAP: RED CROSS BLOOD BANK MANAGEMENT SYSTEM**
======================================================

**ABOUT THE PROJECT**
-----------------
Project Lingap is a web-based Blood Bank Management System developed specifically for the Red Cross Cavite Chapter. The platform digitizes and streamlines the critical operations of a blood bank, facilitating the coordination between blood donors, Red Cross staff, and emergency blood requests.

The system replaces manual logging with a secure, centralized database that tracks blood donations, manages inventory levels in real-time, and processes emergency requests from patients and hospitals efficiently.

**BUILT WITH**
----------
* Framework: Django (Python)
* Frontend: HTML5, CSS3, Bootstrap 5
* Database: SQLite (Default)
* Version Control: Git & GitHub

**KEY FEATURES**
------------
1. Authentication & Roles:
   - Secure login and registration.
   - Distinct dashboards for Donors, Red Cross Staff, and Superuser Admins.

2. Donor Management:
   - User profile completion and management.
   - Tracking of personal donation history and blood request history.

3. Inventory Management:
   - Real-time tracking of blood stocks (Available, Reserved, Distributed, Expired).
   - Filterable inventory lists by blood type and status.

4. Blood Request System:
   - Form-based submission for emergency blood requests.
   - Staff workflow to Approve (Reserve stock) or Complete (Distribute stock) requests.

5. Campaign Management:
   - Scheduling and managing blood donation drives.
   - Tracking donor participation in specific campaigns.

6. Volunteer/Staff Management:
   - Admin tools to register and manage Red Cross staff accounts.

**USAGE**
-----
To run this project locally:

1. Clone the repository:
   git clone https://github.com/lawrencecebrero/project-lingap-blood-bank.git

2. Navigate to the project directory:
   cd project-lingap-blood-bank

3. Create and activate a virtual environment:
   python -m venv .venv (Windows: .venv\Scripts\activate | Mac/Linux: source .venv/bin/activate)

5. Install dependencies:
   pip install -r requirements.txt

6. Apply database migrations:
   python manage.py migrate

7. Create a superuser (to access Admin features):
   python manage.py createsuperuser

8. Run the development server:
   python manage.py runserver

9. Open your browser and visit: http://127.0.0.1:8000/

**CONTACT**
-------

Lawrence Cebrero

GitHub: @lawrencecebrero
Email: lawrence.cebrero@cvsu.edu.ph

Project Link: https://github.com/lawrencecebrero/project-lingap-blood-bank
