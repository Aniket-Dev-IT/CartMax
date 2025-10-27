# ⚡ CartMax Quick Start Guide

Get CartMax running in **5 minutes**!

---

## 🚀 30-Second Setup

```bash
# Clone & enter directory
git clone https://github.com/Aniket-Dev-IT/CartMax.git && cd CartMax

# Create & activate virtual environment
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# Install & setup
pip install -r requirements.txt && python manage.py migrate

# Run!
python manage.py runserver
```

**Visit:** `http://127.0.0.1:8000/` ✅

---

## 5️⃣ Full Setup Walkthrough

### Step 1: Prerequisites Check (1 min)
```bash
python --version        # Should be 3.10+
pip --version          # Should be 21.0+
git --version          # Should be 2.0+
```

### Step 2: Clone Repository (30 sec)
```bash
git clone https://github.com/Aniket-Dev-IT/CartMax.git
cd CartMax
```

### Step 3: Virtual Environment (1 min)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies (2 min)
```bash
pip install -r requirements.txt
```

### Step 5: Database Setup (1 min)
```bash
# Run migrations
python manage.py migrate

# Create admin account (follow prompts)
python manage.py createsuperuser

# Load sample data
python manage.py populate_store_fixed
```

### Step 6: Launch Server (30 sec)
```bash
python manage.py runserver
```

---

## 🎯 What's Next?

### Frontend
- 🏠 **Homepage:** http://127.0.0.1:8000/
- 🛒 **Shop:** http://127.0.0.1:8000/shop/
- 🛍️ **Products:** Browse available items

### Admin Panel
- 🔐 **Admin:** http://127.0.0.1:8000/admin/
- 📊 **Dashboard:** http://127.0.0.1:8000/admin-dashboard/
- **Login:** Use superuser credentials

---

## 📚 Common Commands

| Command | Purpose |
|---------|---------|
| `python manage.py runserver` | Start dev server |
| `python manage.py shell` | Django shell |
| `python manage.py migrate` | Apply migrations |
| `python manage.py createsuperuser` | Create admin |
| `python manage.py collectstatic` | Gather static files |

---

## 🆘 Quick Troubleshooting

### Port 8000 Already in Use?
```bash
python manage.py runserver 8001
```

### Database Issues?
```bash
python manage.py migrate store zero
python manage.py migrate
```

### Static Files Not Loading?
```bash
python manage.py collectstatic --clear --noinput
```

### Virtual Environment Not Activating?
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

---

## 🌐 Default Credentials

**Admin Account:** Create during `createsuperuser` step

**Sample Products:** Auto-loaded via `populate_store_fixed`
- 100+ products
- 10 categories
- Multiple currencies (INR/USD)

---

## 📖 Learn More

- **Full Setup:** [README.md](README.md)
- **Features:** [FEATURES.md](FEATURES.md)
- **Development:** [DEVELOPMENT.md](DEVELOPMENT.md)
- **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Docs:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 💡 Tips

✨ **Set Currency:** Profile → Settings → Currency Preference  
✨ **Add Products:** Admin Panel → Store → Products → Add  
✨ **Manage Orders:** Admin Dashboard → Order Management  
✨ **Create Coupons:** Admin Dashboard → Coupons  

---

## 🎓 First-Time Tips

1. **Explore the UI** - Get familiar with the homepage and shopping flow
2. **Create test products** - Add a few products to see them in action
3. **Test checkout** - Try adding items to cart and checking out
4. **Check admin panel** - Explore the comprehensive admin dashboard
5. **Read documentation** - Check out the guides for deeper understanding

---

## 🤝 Need Help?

- 📖 Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 💬 Open an [issue on GitHub](https://github.com/Aniket-Dev-IT/CartMax/issues)
- 📧 Email: aniket.kumar.devpro@gmail.com

---

**Happy coding! 🚀**
