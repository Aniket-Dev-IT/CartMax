# 🛒 CartMax  E-Commerce Platform

[![Django](https://img.shields.io/badge/Django-4.2.17-darkgreen.svg?style=flat-square)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.2-purple.svg?style=flat-square)](https://getbootstrap.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue.svg?style=flat-square)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-orange.svg?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Fully%20Ready-success.svg?style=flat-square)]()

> **A scalable e-commerce platform featuring dual-currency support (INR & USD), advanced product management, intelligent inventory tracking, and a sophisticated admin dashboard.**

CartMax is a comprehensive Django-powered e-commerce solution designed for businesses looking to establish a online presence. Built with enterprise-grade features, responsive design, and seamless user experience, CartMax supports both Indian Rupee (₹) and US Dollar ($) transactions out of the box.


---

## 🎯 Overview

CartMax is not just another e-commerce platform—it's a complete, production-ready solution for online retail. With support for multiple currencies, intelligent product recommendations, comprehensive inventory management, and a sophisticated admin interface, CartMax empowers businesses to manage their online store efficiently.

**Key Highlights:**
- ✅ **Dual-Currency Support**: Seamlessly switch between INR (₹) and USD ($)
- ✅ **100+ Pre-loaded Products**: Ready to customize across 10 product categories
- ✅ **UI/UX**:  design with glass-morphism effects and smooth animations
- ✅ **Mobile-First Design**: Works perfectly on smartphones, tablets, and desktops
- ✅ **Enterprise Features**: Inventory management, analytics, and advanced reporting
- ✅ **Developer-Friendly**: Clean code structure, well-documented, easy to extend

---

## 🌟 Key Features

### 🌍 **Dual-Currency System**
Switch seamlessly between Indian Rupee (₹) and US Dollar ($) with real-time price conversion. Users can set their preferred currency in their profile, and all prices, cart totals, and orders will automatically display in their chosen currency. Perfect for international e-commerce operations.

### 🛍️ **Advanced Shopping Experience**
Browse through 10 carefully organized product categories with 100+ pre-loaded items. Advanced filtering by price, brand, color, size, and more. Full-text search with intelligent keyword matching. Product gallery with zoom functionality and high-quality images for each item.

### 💳 **Smart Checkout & Payment**
Multi-step checkout process with order summary, shipping information, and payment options. Built-in coupon/discount system with automatic calculation. Apply discount codes for dynamic price adjustments. Multiple payment methods support ready for integration.

### 👤 **Comprehensive User Management**
Secure registration and authentication system with email verification. Complete user profiles with address book, preferences, and purchase history. Session-based carts for guests and persistent carts for registered users. Quick profile access to view and edit account details.

### 📦 **Real-Time Inventory Management**
Track stock levels across your entire product catalog. Automatic low-stock alerts when inventory drops below thresholds. Complete inventory movement history with purchase, sale, and adjustment tracking. Stock status displayed prominently on product pages and admin dashboard.

### ❤️ **Wishlists & Product Comparison**
Save favorite products to wishlists (works for both logged-in users and guests). Compare up to 4 products side-by-side with detailed specifications. Wishlist items can be quickly added to cart for faster checkout.

### ⭐ **Review & Rating System**
Customers can leave detailed reviews with 1-5 star ratings. Display average ratings and review counts on product pages. Admin moderation for reviewing and approving customer feedback. Helpful votes on reviews to highlight the most useful feedback.

### 🎯 **Intelligent Product Recommendations**
Multiple recommendation algorithms including similar products, frequently bought together, and popular items. Personalized recommendations based on user browsing and purchase history. Trending products section showing what's hot right now.

### 📊 **Sophisticated Admin Dashboard**
Comprehensive dashboard with key metrics and statistics. Full product catalog management with bulk operations. Order tracking and status updates with customer notifications. User management and analytics reporting. Coupon and discount code management with usage tracking.

### 📱 **Fully Responsive Design**
Mobile-first approach ensuring perfect display on all devices. Touch-friendly interface with optimized buttons and navigation. Responsive product grids that adapt to screen size. Optimized images and lazy loading for fast performance.

---

## 📸 Screenshots & Demo

### 🏠 **Homepage**
The welcome screen features a stunning hero section with featured categories, a carousel of promotions, and a showcase of popular products. The intuitive navigation bar makes browsing effortless, while the search bar provides quick access to find exactly what you're looking for.

![Home page](static/snap/Home%20page.png)

---

### 👤 **User Profile Management**
A comprehensive profile page where users can manage their account details, shipping addresses, payment methods, and view their complete order history. Users can easily update their preferred currency, personal information, and contact details all in one secure location.

![User Profile](static/snap/User%20Profile.png)

---

### 📋 **Order History & Management**
Track all your orders from one convenient location. View order status (pending, processing, shipped, delivered), order dates, totals, and quick access to order details. The order history supports filtering and sorting for easy navigation through multiple purchases.

![Orders](static/snap/Orders.png)

---

### 📦 **Order Details Page**
Detailed order information includes itemized product list with quantities and prices, shipping address, payment method, applied discounts, tax calculations, and order total. Track order status and view estimated delivery dates. Easy access to customer service contact for any order inquiries.

![Order Info](static/snap/Order%20Info.png)

---

### ✅ **Order Success Confirmation**
After successful checkout, customers receive a beautiful confirmation page showing their unique order ID, order summary with all items, total amount paid, and estimated delivery information. A printable version is available for records.

![Order Success](static/snap/Order%20Success.png)

---

### 📊 **Admin Dashboard**
The administration interface provides a complete overview of your e-commerce operations at a glance. Dashboard displays key metrics including total sales, number of orders, active users, and popular products. Quick action buttons provide rapid access to common admin tasks.

![Admin Dashboard](static/snap/Admin%20Dashboard.png)

---

### 🛠️ **Admin Product Management**
Full product management interface allowing administrators to add, edit, and delete products. Bulk operations for managing multiple products simultaneously. Features include product details (name, description, prices in both currencies), inventory levels, images, categories, and search keywords. Comprehensive filter and search options for finding specific products quickly.

![Admin Products Management](static/snap/Admin%20Products%20Management.png)

---

### 💰 **Dual-Currency Pricing Dashboard**
Experience the flexibility of CartMax's dual-currency system. Prices are automatically displayed in your preferred currency (INR or USD) with real-time conversions. The pricing dashboard shows product costs, discounts, and totals in both currencies side-by-side for complete transparency.

![Pricing Dashboard INR & USD](static/snap/Pricing%20Dashboard%20INR%20%26%20USD.png)

---

## 🛠️ Tech Stack

### **Backend Framework**
- **Django 4.2.17**: Latest stable version of the Django web framework
- **Python 3.10+**:  Python for robust backend logic

### **Frontend Technologies**
- **HTML5**: Semantic markup and progressive enhancement
- **CSS3**:  styling with animations and transitions
- **JavaScript (ES6+)**: Interactive features and AJAX functionality
- **Bootstrap 5.3.2**: Responsive grid system and pre-built components

### **Database**
- **SQLite**: Development database (included, no setup needed)
- **PostgreSQL-ready**: Easy migration to PostgreSQL for production

### **Key Python Packages**
- **Pillow 10.4.0**: Advanced image processing and optimization
- **Selenium 4.15.2**: Web automation and testing
- **BeautifulSoup4 4.12.2**: HTML/XML parsing for data extraction
- **Requests 2.31.0**: HTTP library for API calls and web scraping
- **fake-useragent 1.4.0**: User-agent rotation for web scraping
- **webdriver-manager 4.0.1**: Automated WebDriver management

### **Frontend Libraries**
- **jQuery 3.7.1**: DOM manipulation and AJAX
- **Font Awesome 6.5.0**: 2000+ icons
- **Animate.css**: Smooth animations and transitions

### **Architecture Pattern**
- **MTV (Model-Template-View)**: Django's interpretation of MVC pattern
- **RESTful API endpoints**: Extensible architecture for mobile apps
- **Modular design**: Easily add new features and modules

---

## 📁 Project Structure

```
CartMax/
├── cartmax/                          # Django Project Configuration
│   ├── settings.py                   # Django settings and configuration
│   ├── urls.py                       # Main URL routing and api endpoints
│   ├── wsgi.py                       # WSGI application entry point
│   └── __init__.py
│
├── store/                            # Main E-Commerce Application
│   ├── models.py                     # Database models (15+ models)
│   │   ├── Product                   # Product with dual-currency pricing
│   │   ├── Category                  # Product categories
│   │   ├── Order & OrderItem         # Order management
│   │   ├── Cart & CartItem           # Shopping cart
│   │   ├── Review                    # Product reviews & ratings
│   │   ├── UserProfile               # Extended user profiles
│   │   ├── Wishlist                  # User wishlists
│   │   ├── InventoryMovement         # Stock tracking
│   │   ├── ProductRecommendation     # AI recommendations
│   │   ├── DiscountCoupon            # Coupon system
│   │   └── More...                   # Additional models
│   │
│   ├── views.py                      # Main business logic (50+ views)
│   ├── api_views.py                  # REST API endpoints
│   ├── admin_views.py                # Admin dashboard views
│   ├── admin.py                      # Django admin configuration
│   ├── urls.py                       # App URL routing
│   ├── admin_urls.py                 # Admin panel routing
│   │
│   ├── pricing_engine.py             # Dual-currency pricing logic
│   ├── coupon_utils.py               # Discount and coupon processing
│   ├── search.py                     # Advanced product search
│   ├── recommendations.py            # Product recommendation algorithms
│   ├── inventory.py                  # Inventory management
│   ├── amazon_scraper.py             # Product data scraping
│   └── management/
│       └── commands/                 # Custom Django commands
│
├── templates/                        # HTML Templates
│   ├── base.html                     # Base template with navbar
│   ├── store/
│   │   ├── homepage.html             # Homepage with hero section
│   │   ├── product_detail.html       # Detailed product page
│   │   ├── product_list.html         # Product catalog with filters
│   │   ├── cart.html                 # Shopping cart interface
│   │   ├── checkout.html             # Multi-step checkout
│   │   ├── order_confirmation.html   # Order success page
│   │   └── order_list.html           # User's order history
│   ├── auth/
│   │   ├── login.html                # Login page
│   │   ├── logout.html               # Logout confirmation
│   │   └── register.html             # Registration page
│   └── admin_dashboard/              # Admin panel templates
│       ├── dashboard.html            # Admin overview
│       ├── product_management.html   # Product CRUD
│       ├── order_management.html     # Order management
│       └── More...
│
├── static/                           # Static Assets
│   ├── css/
│   │   ├── main.css                  # Legacy styles
│   │   ├── cartmax-.css        #  CartMax design system
│   │   └── responsive.css            # Mobile-first responsive styles
│   ├── js/
│   │   ├── main.js                   # Core application logic
│   │   ├── cart.js                   # Shopping cart functionality
│   │   ├── search.js                 # Advanced search features
│   │   └── animations.js             # Smooth animations
│   ├── images/                       # CartMax branding assets
│   ├── icons/                        # Custom icon files
│   └── snap/                         # Project screenshots
│
├── media/                            
│   ├── products/                     
│   │   ├── Automotive/
│   │   ├── Beauty & Personal Care/
│   │   ├── Books/
│   │   ├── Clothing/
│   │   ├── Electronics/
│   │   ├── Grocery & Gourmet Food/
│   │   ├── Health & Wellness/
│   │   ├── Home & Kitchen/
│   │   ├── Sports & Outdoors/
│   │   └── Toys & Games/
│   └── user_uploads/                 # User profile pictures
│
├── manage.py                         # Django management CLI
├── requirements.txt                  # Python dependencies
├── db.sqlite3                        # SQLite 
├── README.md                         # This file
└── .gitignore                        # Git ignore rules
```

---

## 🎨 Design System

### **Color Palette**
CartMax uses a , color scheme that stands out from generic e-commerce platforms:

| Color | Usage | Hex Code |
|-------|-------|----------|
| **Sky Blue** | Primary brand color, buttons, links | `#0ea5e9` |
| **Purple** | Accent color, highlights, CTAs | `#d946ef` |
| **White** | Background, cards, text areas | `#ffffff` |
| **Dark Gray** | Primary text, headings | `#1f2937` |
| **Light Gray** | Secondary text, borders | `#e5e7eb` |
| **Success Green** | Confirmations, success messages | `#10b981` |
| **Alert Red** | Errors, warnings, critical alerts | `#ef4444` |

### **Typography**
- **Primary Font**: Inter (clean, , highly readable)
- **Secondary Font**: Poppins (friendly, slightly rounded for headings)
- **Heading Sizes**: H1 (2.5rem) → H6 (1rem)
- **Body Text**: 1rem (16px) for comfortable reading
- **Line Height**: 1.6 for better readability

### **Component Library**
- **Buttons**: Primary, secondary, outline, and ghost variants
- **Cards**: Product cards, order cards, with hover animations
- **Forms**: Styled inputs with floating labels, error messages
- **Modals**: Product quick-view, confirm dialogs
- **Badges**: Status indicators (pending, shipped, delivered)
- **Loading States**: Spinners, skeleton loaders, progress bars

### **Responsive Breakpoints**
- **Mobile**: 320px - 640px (phones)
- **Tablet**: 641px - 1024px (tablets, small laptops)
- **Desktop**: 1025px+ (desktops, large screens)
- **Ultra-wide**: 1920px+ (cinema displays)

### **UI/UX Principles**
✨ **Glass-morphism Effect**: Frosted glass card backgrounds  
✨ **Smooth Animations**: 300ms transitions for all interactive elements  
✨ **Micro-interactions**: Subtle feedback for user actions  
✨ **Accessibility**: WCAG 2.1 AA compliant color contrasts  
✨ **Performance**: Optimized CSS with minimal animations on mobile  

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.10 or higher
- pip (Python package manager)
- Git (for version control)
- Virtual environment (venv or virtualenv)

### **Step 1: Clone the Repository**
```bash
# Navigate to your desired directory
cd your-projects-folder

# Clone CartMax repository
git clone https://github.com/yourusername/CartMax.git
cd CartMax
```

### **Step 2: Set Up Virtual Environment (Windows)**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

### **Step 2: Set Up Virtual Environment (macOS/Linux)**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### **Step 4: Database Setup**
```bash
# Apply all database migrations
python manage.py migrate

# Create superuser account (admin credentials)
python manage.py createsuperuser
# You'll be prompted to enter:
# - Username (e.g., admin)
# - Email address
# - Password (recommended: strong password)
# - Confirm password

# Populate database with 100 sample products
python manage.py populate_store_fixed
```

### **Step 5: Run Development Server**
```bash
# Start the development server
python manage.py runserver

# Server will start at http://127.0.0.1:8000/
```

### **Step 6: Access CartMax**
- **Frontend**: Open browser and visit `http://127.0.0.1:8000/`
- **Admin Panel**: Visit `http://127.0.0.1:8000/admin/`
- **Admin Dashboard**: Visit `http://127.0.0.1:8000/admin-dashboard/`

---

## 📖 Usage Guide

### **For End Users**

#### **1. Browsing Products**
- Visit the homepage to see featured products and categories
- Use the search bar to find specific products quickly
- Click on any product to view full details, specifications, and customer reviews
- Use filters (price, brand, color, size) to narrow down results

#### **2. Shopping Cart**
- Click "Add to Cart" on product pages to add items
- View cart by clicking the cart icon in the header
- Adjust quantities or remove items from the cart interface
- Apply coupon codes for discounts before checkout

#### **3. Wishlist**
- Click the heart icon on product cards to add items to your wishlist
- Access your wishlist from your profile menu
- Move wishlist items to cart with one click
- Remove items you no longer want

#### **4. Product Comparison**
- Select up to 4 products to compare side-by-side
- View detailed specifications, prices, and ratings in comparison view
- Make informed purchasing decisions based on feature comparison

#### **5. Checkout Process**
- Review cart and apply discount codes
- Enter shipping address (can be saved to profile)
- Select preferred payment method
- Review order summary with itemized costs, tax, and total
- Complete purchase and receive order confirmation

#### **6. Account Management**
- Create an account for faster checkout and order tracking
- Update profile information and add multiple shipping addresses
- Set currency preference (INR or USD)
- View complete order history with status tracking
- Leave reviews and ratings on purchased products

### **For Admin Users**

#### **1. Access Admin Panel**
- Navigate to `http://127.0.0.1:8000/admin/`
- Log in with superuser credentials
- Use Django Admin or CartMax Admin Dashboard (`/admin-dashboard/`)

#### **2. Product Management**
- Add new products with full details (name, description, prices, images)
- Edit existing products and update inventory
- Manage product categories and subcategories
- Add product specifications and detailed descriptions
- Upload multiple product images and set featured images
- Bulk edit products for mass operations

#### **3. Inventory Control**
- Monitor stock levels across all products
- Set low-stock alerts and thresholds
- View complete inventory movement history
- Track stock changes from purchases, returns, and adjustments
- Generate inventory reports for analysis

#### **4. Order Management**
- View all customer orders with detailed information
- Update order status (pending → processing → shipped → delivered)
- Generate invoice and packing slips
- Process refunds and handle cancellations
- Export order data for accounting purposes

#### **5. Customer Management**
- View all registered customer accounts
- Manage customer information and contact details
- View customer order history and preferences
- Manage customer support tickets and complaints

#### **6. Coupon & Discount Management**
- Create discount coupons with custom codes
- Set expiration dates and usage limits
- Define discount amounts (fixed or percentage)
- Track coupon usage and effectiveness
- Manage promotional campaigns

#### **7. Review & Rating Moderation**
- View customer reviews and ratings
- Approve or reject customer reviews
- Respond to customer feedback
- Manage review moderation queue

#### **8. Analytics & Reporting**
- View sales trends and revenue reports
- Analyze customer behavior and preferences
- Generate product performance reports
- Export data for business intelligence tools

---

## 📊 Admin Dashboard

The CartMax Admin Dashboard provides a complete overview of your e-commerce operations:

### **Dashboard Overview**
- **Total Sales**: Revenue generated (all time / selected period)
- **Orders**: Total orders with breakdown by status
- **Customers**: Active users and new registrations
- **Products**: Total inventory, low stock alerts
- **Reviews**: Pending moderation, average ratings

### **Quick Actions**
- ➕ Add New Product
- 📋 Create Discount Coupon
- 👥 View New Customers
- 📦 Process Pending Orders
- ⭐ Review Customer Feedback

### **Management Sections**
- **Products**: Full CRUD operations with bulk actions
- **Categories**: Organize product taxonomy
- **Orders**: Track and manage customer orders
- **Customers**: User management and analytics
- **Coupons**: Create and manage discount codes
- **Reviews**: Moderation and approval queue
- **Inventory**: Stock tracking and alerts
- **Reports**: Sales, revenue, and performance analytics

---

## 🌐 Deployment

### **Environment Configuration**

#### **Step 1: Prepare Environment Variables**
Create a `.env` file in the project root:
```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:port/dbname
ADMIN_EMAIL=admin@yourdomain.com
```

#### **Step 2: Database Migration to PostgreSQL (Production)**
```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update DATABASE settings in settings.py
# Run migrations on new database
python manage.py migrate
python manage.py populate_store_fixed  # Optional: populate sample data
```

#### **Step 3: Collect Static Files**
```bash
# Collect all static files into STATIC_ROOT
python manage.py collectstatic --noinput

# For production, consider using CloudFront or CDN
```

### **Security Checklist**
- [ ] Set `DEBUG = False` in production settings
- [ ] Use a strong, random `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Enable HTTPS/SSL certificate
- [ ] Set `SECURE_SSL_REDIRECT = True`
- [ ] Configure CSRF_TRUSTED_ORIGINS
- [ ] Use environment variables for sensitive data
- [ ] Enable security headers (HSTS, X-Frame-Options, etc.)
- [ ] Configure proper database backups
- [ ] Set up monitoring and logging

### **Recommended Hosting Platforms**

#### **Heroku** (Easiest for beginners)
```bash
# Install Heroku CLI
# Create Procfile
web: gunicorn cartmax.wsgi

# Deploy
git push heroku main
```

#### **DigitalOcean** (Good balance)
- Create Ubuntu droplet
- Install Python, PostgreSQL, nginx
- Use Gunicorn as application server
- Configure nginx as reverse proxy

#### **AWS** (Enterprise-grade)
- Use EC2 for application server
- RDS for managed PostgreSQL database
- S3 for media file storage
- CloudFront for CDN distribution

#### **PythonAnywhere** (Specialized for Python)
- Web-based Django deployment
- Built-in SSL certificates
- Easy database management
- Automatic HTTPS support

#### **Deployment with Gunicorn & Nginx**
```bash
# Install production server
pip install gunicorn whitenoise

# Run Gunicorn
gunicorn cartmax.wsgi:application --bind 0.0.0.0:8000

# Configure nginx as reverse proxy
# Point domain to application
```

### **Performance Optimization**
- Enable caching: `python manage.py cache_clear`
- Use CDN for static files and images
- Implement database connection pooling
- Enable query caching and select_related()
- Compress responses with gzip
- Use Redis for session and cache storage
- Monitor with tools like New Relic or Datadog

### **Monitoring & Logging**
- Set up error tracking (Sentry, Rollbar)
- Configure application logging
- Monitor server resources (CPU, memory, disk)
- Track database performance
- Set up alerts for critical errors

---

## 🤝 Contributing

### **How to Contribute**

We welcome contributions to CartMax! Here's how you can help:

#### **1. Fork the Repository**
```bash
# Click "Fork" button on GitHub
# Clone your forked repository
git clone https://github.com/yourusername/CartMax.git
cd CartMax
```

#### **2. Create a Feature Branch**
```bash
# Create branch for your feature
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

#### **3. Make Your Changes**
- Write clean, well-documented code
- Follow Django best practices
- Add comments for complex logic
- Test your changes thoroughly

#### **4. Commit and Push**
```bash
# Commit with descriptive messages
git commit -m "Add: feature description"
git push origin feature/your-feature-name
```

#### **5. Create Pull Request**
- Go to GitHub and create a Pull Request
- Describe your changes and why they're needed
- Link any related issues
- Wait for code review

### **Code Style Guidelines**
- Use PEP 8 for Python code
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Add docstrings to all functions and classes

### **Reporting Bugs**
- Check if the bug has already been reported
- Provide a clear, descriptive title
- Include steps to reproduce the issue
- Share your system information
- Attach screenshots if applicable
- Include error messages and logs

### **Feature Requests**
- Suggest new features or improvements
- Explain use cases and benefits
- Discuss implementation approach
- Be open to feedback and discussion

### **Development Areas for Contribution**
- 🔐 Payment gateway integration (Stripe, PayPal)
- 📧 Email notification system
- 🤖 Advanced recommendation engine
- 🏪 Multi-vendor marketplace features
- 📱 Mobile app development (React Native/Flutter)
- 🔍 Elasticsearch integration for better search
- 📊 Advanced analytics dashboard
- 🌐 Multi-language support (i18n)
- 🚀 Performance optimization
- 🧪 Unit and integration tests

---

## 📄 License

CartMax is open source and licensed under the **MIT License**. 

You are free to:
- ✅ Use this project for commercial purposes
- ✅ Modify the source code
- ✅ Distribute the software
- ✅ Use it privately

You must:
- ✅ Include the license notice
- ✅ State changes made to the code
- ✅ Include a copy of the license

**See LICENSE file for full details.**

---

## 🆘 Support & Troubleshooting

### **Common Issues**

#### **Issue: Database migration errors**
```bash
# Solution: Reset migrations
python manage.py migrate store zero
python manage.py migrate
```

#### **Issue: Static files not loading**
```bash
# Solution: Collect static files
python manage.py collectstatic --clear --noinput
```

#### **Issue: Permission denied errors**
```bash
# Solution: Check file permissions
chmod -R 755 CartMax/
```

#### **Issue: Port 8000 already in use**
```bash
# Solution: Use different port
python manage.py runserver 8001
```

#### **Issue: Admin account locked/lost**
```bash
# Solution: Create new superuser
python manage.py createsuperuser
```

### **Performance Issues**

#### **Slow page load times**
- Check database queries in Django debug toolbar
- Enable caching: Configure CACHES in settings.py
- Use select_related() and prefetch_related() for queries
- Compress images and use CDN
- Enable gzip compression in nginx

#### **High memory usage**
- Monitor with: `htop` or system monitor
- Check for memory leaks in code
- Use pagination for large datasets
- Clear old logs and temporary files

#### **Database performance**
- Add indexes to frequently queried fields
- Monitor query execution time
- Use database query profiler
- Archive old data to separate table
- Consider database replication for high load

### **Getting Help**

1. **Documentation**: Check Django and CartMax documentation
2. **Stack Overflow**: Search for similar issues
3. **GitHub Issues**: Check existing issues or create new one
4. **Community Forums**: Ask in Django community forums
5. **Email Support**: Contact development team

---

## 🎓 Learning Resources

### **Django Resources**
- [Official Django Documentation](https://docs.djangoproject.com/)
- [Django for Beginners](https://djangoforbeginners.com/)
- [Real Python Django Tutorials](https://realpython.com/django/)

### **Frontend Resources**
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
- [MDN Web Docs](https://developer.mozilla.org/)
- [CSS Tricks](https://css-tricks.com/)

### **E-Commerce Best Practices**
- [Shopify E-Commerce Playbook](https://www.shopify.com/)
- [UX Laws for E-Commerce](https://www.baymard.com/)
- [Payment Security Standards (PCI DSS)](https://www.pcisecuritystandards.org/)

---

## 🚀 Future Roadmap

### **Upcoming Features**
- 🔄 Real-time order notifications (WebSocket support)
- 💰 Payment gateway integration (Stripe, PayPal, RazorPay)
- 📧 Automated email campaigns and notifications
- 🤖 AI-powered product recommendations
- 🌍 Multi-language support (i18n)
- 📱 Native mobile apps (iOS/Android)
- 🔐 Two-factor authentication (2FA)
- 📊 Advanced business intelligence dashboard
- 🏪 Multi-seller marketplace features
- 🚚 Shipping integration (FedEx, UPS, DHL)

---

## Acknowledgments

CartMax is built with love using:
- **Django**: For the powerful web framework
- **Bootstrap**: For responsive design system
- **Font Awesome**: For beautiful icons
- **Open Source Community**: For inspiration and support

### **Contributors**
Special thanks to all contributors who have helped improve CartMax!

---

## 👨‍💻 Connect with the Developer

**CartMax** is developed and maintained by **Aniket Kumar**. 

### **Important Notice - Proprietary License**
⚠️ **CartMax is proprietary software** and is NOT open source. This software is protected by copyright law. You may NOT use, fork, clone, or redistribute this project without obtaining **explicit written permission** from the copyright holder.

The presence of this software on GitHub does NOT grant you any rights to use it. To request permission to use CartMax, please contact the developer directly.

### **Developer Contact Information**

📧 **Email**: [aniket.kumar.devpro@gmail.com](mailto:aniket.kumar.devpro@gmail.com)  
📱 **WhatsApp**: [+91 8318601925](https://wa.me/918318601925)  
🐙 **GitHub**: [@Aniket-Dev-IT](https://github.com/Aniket-Dev-IT)  

**For inquiries about licensing or permission to use CartMax, please reach out via email or WhatsApp.**

---

## 📞 Contact & Information

- **Project Repository**: [GitHub - CartMax](https://github.com/yourusername/CartMax)
- **Issues & Bugs**: [GitHub Issues](https://github.com/yourusername/CartMax/issues)
- **Email**: support@cartmax.com
- **Website**: [CartMax Official](https://www.cartmax.com)

---

<div align="center">

### ⭐ If you find CartMax helpful, please give it a star! ⭐

Made with ❤️ by Aniket Kumar

**Happy Codeing! 🎉**

</div>

---

