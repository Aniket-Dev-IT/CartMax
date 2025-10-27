# 🆘 CartMax Troubleshooting Guide

Solutions to common issues and error messages.

---

## 🔧 Installation & Setup Issues

### Issue: Python version not compatible
**Error:** `Python 3.10+ required`

**Solution:**
```bash
# Check your Python version
python --version

# If version is < 3.10:
# 1. Download Python 3.10+ from python.org
# 2. Install the new version
# 3. Set it as your default or use:
python3.10 -m venv venv
```

### Issue: Virtual environment won't activate
**Error:** `venv\Scripts\activate is not recognized`

**Solution (Windows):**
```powershell
# Try with different syntax:
& '.\venv\Scripts\Activate.ps1'

# Or use the batch file:
venv\Scripts\activate.bat

# Or use python directly:
python -m venv venv
python -m venv --upgrade venv
```

**Solution (macOS/Linux):**
```bash
# Make script executable:
chmod +x venv/bin/activate

# Then activate:
source venv/bin/activate
```

### Issue: `pip install -r requirements.txt` fails
**Error:** `No module named pip` or install errors

**Solution:**
```bash
# Upgrade pip first:
python -m pip install --upgrade pip

# Then install requirements:
pip install -r requirements.txt

# If specific package fails, install individually:
pip install Django==4.2.17
pip install Pillow==10.4.0
# ... continue with other packages
```

---

## 🗄️ Database Issues

### Issue: Migration errors
**Error:** `psycopg2.OperationalError` or migration conflicts

**Solution:**
```bash
# Reset migrations to initial state:
python manage.py migrate store zero

# Then re-apply all migrations:
python manage.py migrate

# Create new superuser:
python manage.py createsuperuser

# Load sample data:
python manage.py populate_store_fixed
```

### Issue: Database locked
**Error:** `database is locked` (SQLite)

**Solution:**
```bash
# SQLite issue - usually from multiple processes
# 1. Stop all Django processes
# 2. Remove lock file if it exists:
rm db.sqlite3-journal

# 3. Restart Django
python manage.py runserver
```

### Issue: Permission denied on database
**Error:** `permission denied` when accessing db.sqlite3

**Solution (Linux/macOS):**
```bash
# Fix permissions:
chmod 644 db.sqlite3
chmod 755 .

# Or with recursive:
chmod -R 755 CartMax/
```

**Solution (Windows):**
```powershell
# Run as Administrator:
icacls db.sqlite3 /grant:r "Users:(F)"
```

---

## 🌐 Server & Port Issues

### Issue: Port 8000 already in use
**Error:** `Address already in use: 127.0.0.1:8000`

**Solution:**
```bash
# Use a different port:
python manage.py runserver 8001

# Or find and kill the process using port 8000:
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :8000
kill -9 <PID>
```

### Issue: Cannot connect to server
**Error:** `Connection refused` or `localhost refused to connect`

**Solution:**
```bash
# Make sure Django server is running:
python manage.py runserver

# Check if it's listening:
# Windows:
netstat -ano | findstr LISTENING

# macOS/Linux:
lsof -i :8000

# Try with explicit IP:
python manage.py runserver 0.0.0.0:8000
```

---

## 📁 Static Files Issues

### Issue: Static files not loading (404 errors)
**Error:** CSS, JS, images showing 404 in browser

**Solution:**
```bash
# Collect all static files:
python manage.py collectstatic --clear --noinput

# Enable static files serving in development:
# Make sure DEBUG = True in settings.py

# Check if STATIC_URL is correct:
# In settings.py should be:
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
```

### Issue: Media files not displaying
**Error:** User uploads, product images showing broken

**Solution:**
```bash
# Ensure media directory exists:
mkdir -p media/products

# Check MEDIA settings in settings.py:
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# In urls.py, make sure media is served:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 🔐 Authentication Issues

### Issue: Cannot login to admin panel
**Error:** `Invalid username or password`

**Solution:**
```bash
# Create a new superuser:
python manage.py createsuperuser

# Follow the prompts for username, email, password

# Or reset password for existing user in shell:
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='admin')
>>> user.set_password('newpassword')
>>> user.save()
>>> exit()
```

### Issue: Session not persisting
**Error:** Getting logged out constantly

**Solution:**
```python
# In settings.py, ensure session settings are correct:
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = False

# Run migrations to create sessions table:
python manage.py migrate
```

---

## 💻 Performance Issues

### Issue: Slow page loads
**Error:** Pages taking too long to load

**Solution:**
```bash
# Enable Django Debug Toolbar:
pip install django-debug-toolbar

# Check database queries being executed
# Optimize query using select_related() and prefetch_related()

# Enable caching:
pip install django-redis

# Compress static files:
python manage.py collectstatic --compress

# Use pagination for large datasets
```

### Issue: High memory usage
**Error:** Server consuming too much RAM

**Solution:**
```bash
# Monitor memory:
# Windows: Task Manager
# Linux: top, htop, free -h
# macOS: Activity Monitor

# Clear old logs:
rm -f *.log logs/*.log

# Clear temporary files:
python manage.py clear_cache
python manage.py clearsessions

# Use database pagination instead of loading all data
```

---

## 🛒 E-Commerce Specific Issues

### Issue: Products not showing in shop
**Error:** Homepage shows no products

**Solution:**
```bash
# Check if products exist in database:
python manage.py shell
>>> from store.models import Product
>>> Product.objects.count()
>>> Product.objects.all()[:5]

# If count is 0, load sample data:
python manage.py populate_store_fixed
```

### Issue: Cart not persisting
**Error:** Items removed from cart after refresh

**Solution:**
```python
# In settings.py, ensure session is enabled:
INSTALLED_APPS = [
    'django.contrib.sessions',  # Must be included
    # ... other apps
]

# Check if user is logged in before assuming persistence:
# Guest users should use session-based cart
```

### Issue: Checkout failing
**Error:** Cannot complete order

**Solution:**
```bash
# Check for validation errors:
python manage.py shell
>>> from store.models import Order
>>> Order.objects.latest('created_at')

# Verify shipping address is provided
# Check payment gateway configuration

# Look for error logs:
tail -f django.log
```

---

## 🔍 Search Issues

### Issue: Search returning no results
**Error:** No products found when searching

**Solution:**
```bash
# Check if search index is updated:
python manage.py shell
>>> from store.models import Product
>>> p = Product.objects.get(id=1)
>>> p.name  # Verify product exists

# Reindex search:
python manage.py rebuild_index

# Check search implementation in store/search.py
```

---

## 🔄 API Issues

### Issue: API endpoints returning 404
**Error:** `404 Not Found` for API calls

**Solution:**
```bash
# Verify API URLs are registered in urls.py:
# Check store/api_urls.py is included in main urls.py

# Test API endpoint:
curl http://127.0.0.1:8000/api/products/

# If using authentication, ensure session exists:
curl -b cookies.txt -c cookies.txt http://127.0.0.1:8000/api/auth/login/
```

### Issue: CORS errors
**Error:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution:**
```bash
# Install django-cors-headers:
pip install django-cors-headers

# In settings.py:
INSTALLED_APPS = [
    'corsheaders',
    # ... other apps
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... other middleware
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
```

---

## 🐛 Common Error Messages

### `ModuleNotFoundError: No module named 'X'`
**Cause:** Package not installed

**Fix:**
```bash
pip install package_name
```

### `TemplateDoesNotExist: X.html`
**Cause:** Template file not found

**Fix:**
```bash
# Check TEMPLATES setting in settings.py
# Ensure template directory is configured correctly
# Verify file exists in templates/ directory
```

### `ImproperlyConfigured: SECRET_KEY is not set`
**Cause:** Django configuration error

**Fix:**
```python
# In settings.py:
SECRET_KEY = 'your-secret-key-here'
# Or generate new:
from django.core.management.utils import get_random_secret_key
SECRET_KEY = get_random_secret_key()
```

### `DisallowedHost at /`
**Cause:** Host not in ALLOWED_HOSTS

**Fix:**
```python
# In settings.py:
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'yourdomain.com']
```

---

## 📝 Debug Mode

### Enable Debug Mode
```python
# In settings.py:
DEBUG = True

# This shows detailed error pages
# ⚠️ NEVER use in production!
```

### View Error Logs
```bash
# Windows:
type django.log

# macOS/Linux:
cat django.log
tail -f django.log  # Real-time
```

### Run Django Shell
```bash
python manage.py shell

# Useful for debugging:
>>> from store.models import Product
>>> Product.objects.count()
>>> User.objects.all()
```

---

## 🤝 Getting More Help

If you can't find a solution:

1. **Search issues on GitHub:** https://github.com/Aniket-Dev-IT/CartMax/issues
2. **Check documentation:** [README.md](README.md), [DEVELOPMENT.md](DEVELOPMENT.md)
3. **Open a new issue** with:
   - Clear description of the problem
   - Error message/traceback
   - Steps to reproduce
   - Your environment (OS, Python version, etc.)

4. **Contact developer:**
   - 📧 Email: aniket.kumar.devpro@gmail.com
   - 📱 WhatsApp: +91 8318601925

---

**Last Updated:** October 27, 2025  
**Questions?** Open an issue or contact the developer!
