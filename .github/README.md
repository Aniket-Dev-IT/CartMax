# 🛒 CartMax - Professional E-Commerce Platform

<div align="center">

[![Django](https://img.shields.io/badge/Django-4.2.17-darkgreen.svg?style=for-the-badge)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.2-purple.svg?style=for-the-badge)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-Proprietary-orange.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg?style=for-the-badge)](.)

**A feature-rich, production-ready e-commerce platform with dual-currency support, 100+ products, advanced inventory management, and comprehensive admin dashboard.**

---

### ⭐ If you find this project useful, please give it a star!

[View Documentation](#-features) • [Getting Started](#-quick-start) • [Screenshots](#-screenshots) • [Contribute](#-contributing) • [Contact Developer](#-developer-contact)

</div>

---

## 🚀 What is CartMax?

CartMax is a **complete, enterprise-grade e-commerce solution** built with Django. It's designed for businesses that need a professional online retail platform without the complexity of heavyweight enterprise systems.

### Perfect For:
- 🏪 Online retailers and small-to-medium businesses
- 📱 Startups launching e-commerce ventures
- 💼 Companies wanting a customizable alternative to SaaS platforms
- 👨‍💻 Developers learning advanced Django patterns
- 🎓 Educational projects demonstrating real-world Django applications

---

## ✨ Key Features at a Glance

### 💱 **Dual-Currency Support**
Seamlessly support customers worldwide with automatic USD/INR conversion and currency-specific pricing.

### 🛍️ **Complete Product Catalog**
100+ pre-loaded products across 10 diverse categories, ready for customization and expansion.

### 📊 **Sophisticated Admin Dashboard**
Full control over inventory, orders, customers, coupons, and analytics with an intuitive interface.

### 🔒 **Secure & Scalable**
Enterprise-grade security with SQLite development setup and PostgreSQL production ready.

### 📦 **Smart Inventory Management**
Real-time stock tracking, low-stock alerts, and complete inventory movement history.

### ⭐ **Reviews & Ratings**
Customer feedback system with moderation capabilities and rating aggregation.

### 💳 **Flexible Checkout**
Multi-step checkout with coupon/discount support, multiple payment method readiness, and order tracking.

### 📱 **Mobile-First Responsive Design**
Perfectly optimized for smartphones, tablets, and desktops using Bootstrap 5.

### 🔍 **Advanced Search & Discovery**
Intelligent product search with filters, recommendations engine, and wishlist functionality.

---

## 🎨 Technology Stack

**Backend:**
- Python 3.10+ with Django 4.2.17
- SQLite (dev) / PostgreSQL (prod-ready)
- RESTful API endpoints

**Frontend:**
- HTML5 & CSS3 with glass-morphism effects
- JavaScript (ES6+) with AJAX functionality
- Bootstrap 5.3.2 for responsive grid system
- Font Awesome 6.5.0 for beautiful icons

**Additional Tools:**
- Pillow for image processing
- Selenium for web automation
- BeautifulSoup4 for data parsing
- XHTML2PDF for PDF generation

---

## 📸 Quick Visual Tour

### Homepage - Featured Products & Categories
![Homepage](../static/snap/Home%20page.png)

### Admin Dashboard - Complete Overview
![Admin Dashboard](../static/snap/Admin%20Dashboard.png)

### Product Management - Full CRUD Operations
![Product Management](../static/snap/Admin%20Products%20Management.png)

### Dual-Currency Pricing - INR & USD Support
![Pricing Dashboard](../static/snap/Pricing%20Dashboard%20INR%20%26%20USD.png)

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Git
- pip (Python package manager)

### Installation (5 minutes)

```bash
# Clone the repository
git clone https://github.com/Aniket-Dev-IT/CartMax.git
cd CartMax

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python manage.py migrate
python manage.py createsuperuser

# Load sample products
python manage.py populate_store_fixed

# Run development server
python manage.py runserver
```

**That's it!** Visit `http://127.0.0.1:8000/` to see CartMax in action.

---

## 📚 Next Steps

- **Full Documentation:** See [README.md](../README.md) for comprehensive setup and usage guide
- **Feature Details:** Check [FEATURES.md](../FEATURES.md) for complete feature documentation
- **Development Guide:** Read [DEVELOPMENT.md](../DEVELOPMENT.md) for contributing
- **Changelog:** View [CHANGELOG.md](../CHANGELOG.md) for version history

---

## 🏗️ Project Structure

```
CartMax/
├── cartmax/              # Django project configuration
├── store/                # Main e-commerce application
│   ├── models.py         # 15+ database models
│   ├── views.py          # 50+ business logic views
│   ├── api_views.py      # REST API endpoints
│   └── admin_views.py    # Admin dashboard
├── templates/            # HTML templates
├── static/               # CSS, JavaScript, images
├── media/                # Product images & uploads
└── manage.py             # Django CLI
```

---

## 💡 Why Choose CartMax?

| Feature | CartMax | Alternative |
|---------|---------|-------------|
| **Setup Time** | 5 minutes | Hours/Days |
| **Customization** | Complete source code | Limited |
| **Cost** | Free (with permission) | $300-$3000+/month |
| **Scalability** | PostgreSQL ready | Built-in scaling |
| **Learning Value** | Excellent Django patterns | Black box |

---

## 🔐 License & Usage

⚠️ **Important:** CartMax is **proprietary software**. It requires explicit written permission from the developer for use.

See [LICENSE](../LICENSE) for full terms.

**To request permission to use CartMax:**
- 📧 Email: [aniket.kumar.devpro@gmail.com](mailto:aniket.kumar.devpro@gmail.com)
- 📱 WhatsApp: [+91 8318601925](https://wa.me/918318601925)
- 🐙 GitHub: [@Aniket-Dev-IT](https://github.com/Aniket-Dev-IT)

---

## 🤝 Contributing

CartMax welcomes contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- 🐛 Reporting bugs
- 💡 Suggesting features
- 🔧 Submitting pull requests
- 📝 Writing documentation

### Development Areas Needed:
- Payment gateway integration (Stripe, PayPal)
- Multi-language support (i18n)
- Advanced analytics dashboard
- Mobile app (React Native/Flutter)

---

## 🆘 Support & Community

- 📖 **Documentation:** Full setup and usage guide in main [README.md](../README.md)
- 🐛 **Issues:** Report bugs on [GitHub Issues](https://github.com/Aniket-Dev-IT/CartMax/issues)
- 💬 **Discussions:** Community Q&A in [GitHub Discussions](https://github.com/Aniket-Dev-IT/CartMax/discussions)
- 📧 **Direct Contact:** Email or WhatsApp the developer

---

## 👨‍💻 About the Developer

**CartMax** is developed and maintained by **Aniket Kumar**, a passionate full-stack Django developer.

- 🐙 **GitHub:** [@Aniket-Dev-IT](https://github.com/Aniket-Dev-IT)
- 📧 **Email:** [aniket.kumar.devpro@gmail.com](mailto:aniket.kumar.devpro@gmail.com)
- 📱 **WhatsApp:** [+91 8318601925](https://wa.me/918318601925)

---

## 📊 Project Statistics

- **Lines of Code:** 5000+
- **Database Models:** 15+
- **API Endpoints:** 30+
- **Admin Views:** 20+
- **Pre-loaded Products:** 100+
- **Product Categories:** 10
- **Supported Currencies:** 2 (INR, USD)
- **Setup Time:** ~5 minutes

---

<div align="center">

### ⭐ Star this repository to show support and help others discover CartMax!

**Made with ❤️ by Aniket Kumar**

[Back to Top](#-cartmax---professional-e-commerce-platform)

</div>
