<div align="center">
  <h1>🖨️ PrintFlow</h1>
  <p><strong>A Modern, Sleek Print Management System for Friend Groups & Small Communities</strong></p>
</div>

<br />

PrintFlow is a beautifully designed Django-based web application that streamlines the process of managing print orders. It allows users to upload documents (PDFs), automatically calculates pricing based on page count and printing preferences, and provides a powerful admin dashboard to manage the print queue and payments.

## ✨ Features

- **📄 Smart Document Handling**: Securely upload PDFs with automatic page count detection.
- **💰 Dynamic Pricing**: Calculates costs instantly based on color, sidedness (single/double), and page count.
- **👥 User Management**: Registration system with an admin approval workflow to ensure only authorized friends can place orders.
- **🎨 Premium UI/UX**: A stunning, responsive interface featuring glassmorphism, smooth animations, and a polished dark theme.
- **📊 Admin Dashboard**: A comprehensive view of all active orders, printed history, and user payment balances.
- **💸 Balance Tracking**: Keeps track of who has paid and who still owes money, complete with one-click "Mark All Paid" functionality.
- **🧹 Auto-Cleanup**: Built-in management commands to automatically delete physical files after 7 days while retaining order history.

## 🚀 Tech Stack

- **Backend**: Python 3, Django 6
- **Database**: SQLite (Development) / Ready for PostgreSQL (Production)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphism Design System)
- **PDF Processing**: `pypdf`
- **Asset Management**: WhiteNoise

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Vyom-Repo/PrintFlow.git
   cd PrintFlow
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (Admin)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```
   *Visit `http://localhost:8000` to see the application in action!*

## 💡 Usage

1. **Users** sign up for an account.
2. **Admin** logs in and approves the new user account from the dashboard.
3. **Users** upload their documents, select print options (Color/B&W, Single/Double sided), and submit their order.
4. **Admin** views the queue, prints the documents directly from the browser, and marks them as "Printed".
5. **Admin** tracks payments and marks orders as "Paid" once the user settles their balance.

## 🧹 Maintenance

To clean up printed document files older than 7 days (to save disk space), run:
```bash
python manage.py cleanup_files
```
*Tip: You can set this up as a daily cron job!*

---
<div align="center">
  <p>Built with ❤️ using Django</p>
</div>
