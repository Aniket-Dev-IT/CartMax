# Development Guide

This guide helps you set up CartMax for local development and contributes changes back to the project.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Git**: [Download Git](https://git-scm.com/download/)
- **pip**: Comes with Python (verify with `python -m pip --version`)
- **Virtual Environment**: Built into Python (venv module)
- **Database**: SQLite (included) or PostgreSQL (optional for development)
- **Text Editor/IDE**: VS Code, PyCharm, or similar

### Verify Installations

```bash
python --version        # Should be 3.10 or higher
git --version          # Any recent version
pip --version          # Any recent version
```

---

## Getting Started

### Step 1: Clone the Repository

```bash
# Clone the CartMax repository
git clone https://github.com/YOUR-USERNAME/CartMax.git
cd CartMax
```

### Step 2: Create Virtual Environment

**On Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install all project dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

Create a `.env` file in the project root:

```bash
# Copy template (if it exists)
cp .env.example .env

# Or create manually with:
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### Step 5: Setup Database

```bash
# Apply all database migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
# Follow prompts to enter username, email, and password

# Load sample data (100+ products)
python manage.py populate_store_fixed
```

### Step 6: Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser to see CartMax running!

### Step 7: Access Admin Panel

Visit `http://127.0.0.1:8000/admin/` and log in with your superuser credentials.

---

## Project Structure

```
CartMax/
├── cartmax/                    # Django project configuration
│   ├── settings.py            # Main settings file
│   ├── urls.py                # Main URL routing
│   ├── wsgi.py                # WSGI entry point
│   └── __init__.py
│
├── store/                      # Main e-commerce application
│   ├── models.py              # Database models (15+ models)
│   ├── views.py               # Main business logic (50+ views)
│   ├── api_views.py           # REST API endpoints
│   ├── admin_views.py         # Admin dashboard views
│   ├── admin.py               # Django admin configuration
│   ├── urls.py                # App URL routing
│   ├── admin_urls.py          # Admin panel routing
│   ├── pricing_engine.py      # Dual-currency pricing logic
│   ├── coupon_utils.py        # Discount processing
│   ├── search.py              # Product search
│   ├── recommendations.py     # Recommendation algorithms
│   ├── inventory.py           # Inventory management
│   ├── amazon_scraper.py      # Data scraping utilities
│   └── management/            # Custom Django commands
│
├── templates/                 # HTML templates
│   ├── base.html             # Base template
│   ├── store/                # Store templates
│   ├── auth/                 # Authentication templates
│   └── admin_dashboard/      # Admin templates
│
├── static/                    # Static assets
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   ├── images/               # Images and icons
│   └── snap/                 # Screenshots
│
├── media/                     # User-uploaded files
│   └── products/             # Product images
│
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── CONTRIBUTING.md            # Contribution guidelines
├── CHANGELOG.md               # Version history
├── SECURITY.md                # Security policy
├── CODE_OF_CONDUCT.md         # Community guidelines
├── LICENSE                    # Project license
└── .gitignore                # Git ignore rules
```

---

## Common Development Tasks

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test store

# Run with verbose output
python manage.py test --verbosity=2

# Run with coverage (if installed)
coverage run --source='.' manage.py test
coverage report
```

### Database Migrations

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# See migration status
python manage.py showmigrations

# Rollback to specific migration
python manage.py migrate store 0001
```

### Creating Admin Commands

Place custom commands in `store/management/commands/your_command.py`:

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Your command description'

    def add_arguments(self, parser):
        parser.add_argument('arg_name', type=str)

    def handle(self, *args, **options):
        self.stdout.write('Running command...')
```

Run with: `python manage.py your_command`

### Static Files

```bash
# Collect static files (production)
python manage.py collectstatic

# Clear static files cache
python manage.py collectstatic --clear --noinput
```

### Shell Commands

```bash
# Open Django shell
python manage.py shell

# Example shell operations:
from store.models import Product
products = Product.objects.all()
products.count()
```

---

## Code Style Guidelines

### Python Code

Follow **PEP 8** with these specific rules:

```python
# Good: Clear, readable code
def calculate_discount(price, discount_percentage):
    """Calculate discounted price."""
    if discount_percentage < 0 or discount_percentage > 100:
        raise ValueError("Discount must be between 0 and 100")
    
    discount_amount = price * (discount_percentage / 100)
    return price - discount_amount


# Bad: Unclear, hard to read
def calc(p, d):
    return p - (p * d / 100)
```

### Django Models

```python
class Product(models.Model):
    """Represents a product in the store."""
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
    
    def is_in_stock(self):
        return self.stock > 0
```

### Django Views

```python
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from store.models import Product

def product_detail(request, product_id):
    """Display detailed product information."""
    product = get_object_or_404(Product, id=product_id)
    related = Product.objects.filter(
        category=product.category
    ).exclude(id=product_id)[:5]
    
    context = {
        'product': product,
        'related_products': related,
    }
    return render(request, 'store/product_detail.html', context)


@login_required
def add_to_cart(request, product_id):
    """Add product to user's cart."""
    # Implementation here
    pass
```

### CSS/JavaScript

```css
/* Use semantic selectors */
.product-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.product-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

```javascript
// Use descriptive names, arrow functions
const addToCart = (productId) => {
    const quantity = parseInt(document.querySelector('.quantity-input').value);
    
    fetch(`/api/cart/add/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ product_id: productId, quantity }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Added to cart!');
        }
    });
};
```

---

## Debugging

### Django Debug Toolbar

```bash
pip install django-debug-toolbar
```

Add to `settings.py`:
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

Add to main `urls.py`:
```python
if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
```

Visit any page and look for the debug toolbar on the right side.

### Print Debugging

```python
# Simple print statements
print(f"Product: {product.name}, Price: {product.price_inr}")

# Use Python logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Django Shell Debugging

```bash
python manage.py shell

# Test queries
from store.models import Product
products = Product.objects.filter(stock__gt=0)
for p in products:
    print(f"{p.name}: ₹{p.price_inr}")
```

### Browser DevTools

- Open browser DevTools (F12)
- **Console**: View JavaScript errors
- **Network**: Check API calls
- **Storage**: Inspect cookies/localStorage
- **Elements**: Inspect HTML structure

---

## Version Control

### Workflow

```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and commit
git add .
git commit -m "Add: amazing feature"

# Push to remote
git push origin feature/amazing-feature

# Create Pull Request on GitHub
# (After PR is merged, delete branch)

git checkout main
git pull origin main
git branch -d feature/amazing-feature
```

### Good Commits

```bash
# Good: Atomic, descriptive
git commit -m "Add: Product search with filters

- Implement full-text search
- Add category filter
- Add price range filter
- Update product_list template
- Add search tests"

# Bad: Too vague
git commit -m "Fixed stuff"
```

---

## Performance Tips

### Database

```python
# Use select_related for ForeignKey
products = Product.objects.select_related('category').all()

# Use prefetch_related for reverse relations
categories = Category.objects.prefetch_related('products').all()

# Use only/defer for specific fields
products = Product.objects.only('id', 'name', 'price_inr')

# Avoid N+1 queries
# Bad:
for product in products:
    print(product.category.name)

# Good:
products = products.select_related('category')
```

### Caching

```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# Cache view for 5 minutes
@cache_page(60 * 5)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

# Cache specific data
cache.set('featured_products', products, 60 * 60)
featured = cache.get('featured_products')
```

---

## Security During Development

### Checklist

- [ ] Never commit `.env` file
- [ ] Use `SECRET_KEY` from environment
- [ ] Keep Django security middleware enabled
- [ ] Never log sensitive data
- [ ] Use parameterized queries (Django ORM)
- [ ] Validate all user inputs
- [ ] Use CSRF tokens in forms
- [ ] Keep dependencies updated

### Check for Vulnerabilities

```bash
# Install and run safety check
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

---

## Troubleshooting

### Issue: Virtual environment not activating

**Solution:**
```bash
# Try full path
.\venv\Scripts\Activate.ps1

# If still fails, check execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Database migration errors

**Solution:**
```bash
# Reset migrations (development only!)
python manage.py migrate store zero
python manage.py migrate

# Or remove db.sqlite3 and recreate
rm db.sqlite3
python manage.py migrate
python manage.py populate_store_fixed
```

### Issue: Static files not loading

**Solution:**
```bash
# Collect static files
python manage.py collectstatic --clear --noinput

# Check STATIC_URL in settings
# Should be: STATIC_URL = '/static/'
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use different port
python manage.py runserver 8001

# Or find and kill process on port 8000
netstat -ano | findstr :8000  # Windows
kill -9 $(lsof -t -i:8000)    # macOS/Linux
```

### Issue: Import errors

**Solution:**
```bash
# Make sure venv is activated
# Check PYTHONPATH
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

---

## Additional Resources

### Official Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Python Documentation](https://docs.python.org/3/)
- [GitHub Git Handbook](https://guides.github.com/)

### Django Tutorials
- [Django for Beginners](https://djangoforbeginners.com/)
- [Real Python Django](https://realpython.com/django/)
- [Django REST Framework](https://www.django-rest-framework.org/)

### Community
- [Django Forum](https://forum.djangoproject.com/)
- [Stack Overflow - django tag](https://stackoverflow.com/questions/tagged/django)
- [r/django on Reddit](https://reddit.com/r/django/)

---

## Getting Help

1. **Check Documentation**: Read README.md and CONTRIBUTING.md
2. **Search Issues**: Look for similar issues on GitHub
3. **Ask Question**: Create a discussion or issue with details
4. **Contact**: Email aniket.kumar.devpro@gmail.com

---

## Next Steps

- [ ] Read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- [ ] Check [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards
- [ ] Review [SECURITY.md](SECURITY.md) for security practices
- [ ] Explore the codebase and models
- [ ] Run tests: `python manage.py test`
- [ ] Start with a simple task or bug fix

Happy coding! 🚀

**Last Updated:** October 27, 2025
