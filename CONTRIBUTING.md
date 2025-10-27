# Contributing to CartMax

Thank you for your interest in contributing to CartMax! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please ensure all interactions remain respectful and professional.

## How to Report Bugs

### Before Submitting a Bug Report

- Check the existing [Issues](https://github.com/Aniket-Dev-IT/CartMax/issues) to avoid duplicates
- Check the [FAQ](docs/FAQ.md) for solutions to common problems
- Check the [Troubleshooting Guide](DEVELOPMENT.md#troubleshooting)
- Verify you're using the latest version

### How to Submit a Bug Report

1. Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)
2. **Clear Title**: Describe the issue in 50 characters or less
3. **Environment**: Include Python version, Django version, OS, and browser
4. **Steps to Reproduce**: Provide exact steps that cause the issue
5. **Expected vs Actual**: Clearly describe expected and actual behavior
6. **Screenshots**: Include screenshots or screen recordings if applicable
7. **Error Messages**: Copy full error messages and stack traces

Example:
```
**Title**: Cart total calculation incorrect with multiple discount codes

**Steps to Reproduce**:
1. Add product to cart
2. Apply first discount code (10% off)
3. Apply second discount code (₹100 off)
4. View cart total

**Expected**: Discounts applied correctly in sequence
**Actual**: Only one discount is being applied
```

## How to Suggest Features

1. Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)
2. **Title**: One sentence summary of the feature
3. **Problem Statement**: Why is this feature needed?
4. **Proposed Solution**: How should this feature work?
5. **Alternatives**: Have you considered alternative approaches?
6. **Additional Context**: Screenshots, mockups, or examples

Example:
```
**Title**: Add email notifications for order status updates

**Problem**: Users can't receive real-time updates about their orders

**Proposed Solution**: Implement automated email notifications when order status changes (processing → shipped → delivered)

**Alternatives**: Could also use in-app notifications or SMS
```

## Pull Request Process

### Before Starting

1. **Fork** the repository
2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/amazing-feature
   # OR
   git checkout -b fix/bug-fix-description
   ```
3. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   ```

### Making Changes

1. **Write clean code** following our style guidelines
2. **Add comments** for complex logic
3. **Update documentation** if you change functionality
4. **Test thoroughly** before submitting
5. **Make atomic commits** with clear messages

### Submitting a Pull Request

1. **Update** the [CHANGELOG.md](CHANGELOG.md) with your changes
2. **Create a pull request** with clear description using the [PR Template](.github/PULL_REQUEST_TEMPLATE.md)
3. **Link related issues**: "Closes #123" or "Fixes #456"
4. **Include screenshots** for UI changes
5. **Be responsive** to review feedback

### Pull Request Checklist

- [ ] Code follows PEP 8 style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts

## Coding Standards

### Python Code Style

We follow **PEP 8** with these conventions:

```python
# Use 4 spaces for indentation
# Maximum line length: 100 characters
# Use meaningful variable names
# Add docstrings to all functions/classes

def calculate_cart_total(cart_items, discount_percentage=0):
    """
    Calculate total price of items in cart.
    
    Args:
        cart_items (list): List of CartItem objects
        discount_percentage (float): Optional discount percentage
        
    Returns:
        float: Total price after discount
    """
    subtotal = sum(item.price * item.quantity for item in cart_items)
    discount = subtotal * (discount_percentage / 100)
    return subtotal - discount
```

### Django Best Practices

- Use `.get()` for single objects with exception handling
- Use `.filter()` for querysets
- Implement `__str__()` method in all models
- Use Django's built-in validation
- Follow MTV (Model-Template-View) pattern
- Use class-based views when appropriate

### JavaScript/CSS

- Use ES6+ features
- Follow existing code style in the project
- Comment complex selectors or functions
- Ensure responsive design works on mobile

### HTML Templates

- Use semantic HTML5
- Include ARIA labels for accessibility
- Maintain consistent indentation
- Use Django template tags properly

## Branch Naming Convention

```
feature/     - New feature (feature/dual-currency-support)
fix/         - Bug fix (fix/cart-calculation-error)
refactor/    - Code refactoring (refactor/search-function)
docs/        - Documentation updates (docs/installation-guide)
test/        - Test additions (test/checkout-flow)
```

## Commit Message Format

```
[TYPE] Brief description (50 chars max)

Detailed explanation of changes (if needed). This should explain
the WHAT and WHY, not the HOW. Keep lines under 72 characters.

Closes #123 (if applicable)
```

Types:
- `Add:` New feature
- `Fix:` Bug fix
- `Refactor:` Code reorganization
- `Docs:` Documentation changes
- `Test:` Test additions/modifications
- `Style:` Formatting, missing semicolons, etc.

Examples:
```
Add: Implement dual currency converter

Implement real-time INR/USD conversion with Exchange Rate API.
Adds conversion toggle to user profile and product pages.

Closes #45

---

Fix: Correct cart total calculation with multiple discounts

Previously, only the last discount was being applied when multiple
coupon codes were used. Now applies all valid discounts in sequence.

Closes #78

---

Docs: Add deployment guide for DigitalOcean

Added comprehensive guide for deploying CartMax on DigitalOcean
with Gunicorn and Nginx configuration examples.
```

## Testing Requirements

### Before Submitting PR

1. **Run existing tests**: Ensure no tests break
2. **Add tests for new features**: Minimum 80% code coverage
3. **Test manually**: Walk through the feature/fix
4. **Cross-browser testing**: Test on Chrome, Firefox, Safari, Edge
5. **Mobile testing**: Test on various screen sizes

### Testing Command

```bash
python manage.py test
```

## Documentation Requirements

### For New Features

1. **Update README.md** if adding major features
2. **Add docstrings** to all functions/classes/modules
3. **Update CHANGELOG.md**
4. **Add inline comments** for complex logic
5. **Create/update related docs** in `/docs` if applicable

### Example Docstring

```python
class ProductRecommendationEngine:
    """
    Recommend products based on user browsing and purchase history.
    
    This engine uses collaborative filtering and content-based
    recommendations to suggest relevant products.
    
    Attributes:
        min_confidence (float): Minimum confidence threshold (0-1)
        max_recommendations (int): Maximum products to recommend
    """
    
    def get_recommendations(self, user, limit=5):
        """
        Generate product recommendations for a user.
        
        Args:
            user (User): The user to generate recommendations for
            limit (int): Maximum number of recommendations
            
        Returns:
            QuerySet: Recommended Product objects
            
        Raises:
            ValueError: If limit is negative
        """
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        # Implementation here
```

## Review Process

1. **Code Review**: At least one maintainer will review your PR
2. **Feedback**: Maintainers may request changes
3. **Revisions**: Address feedback by updating your branch
4. **Approval**: Once approved, a maintainer will merge
5. **Release**: Your contribution will be included in next version

## Development Areas for Contribution

### High Priority
- 🔐 Payment gateway integration (Stripe, PayPal, RazorPay)
- 📧 Email notification system
- 🧪 Unit and integration tests
- 📱 Mobile app (React Native/Flutter)

### Medium Priority
- 🤖 Advanced recommendation engine
- 🏪 Multi-vendor marketplace features
- 🌐 Multi-language support (i18n)
- 🔍 Elasticsearch integration

### Low Priority
- 📊 Advanced analytics dashboard
- 🚚 Shipping integration (FedEx, UPS, DHL)
- 🧠 ML-based product recommendations
- ⚡ Performance optimization

## Development Setup

Detailed setup instructions available in [DEVELOPMENT.md](DEVELOPMENT.md).

Quick start:
```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/CartMax.git
cd CartMax

# Set up environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load sample data
python manage.py populate_store_fixed

# Start development server
python manage.py runserver
```

## Getting Help

- 📚 Check [Documentation](docs/)
- 🐛 Browse [Issues](https://github.com/Aniket-Dev-IT/CartMax/issues)
- 💬 Ask on [Discussions](https://github.com/Aniket-Dev-IT/CartMax/discussions)
- 📧 Email: aniket.kumar.devpro@gmail.com
- 📱 WhatsApp: +91 8318601925

## Recognition

Contributors will be recognized in:
- [CHANGELOG.md](CHANGELOG.md)
- [Contributors List](docs/CONTRIBUTORS.md)
- GitHub Contributors page

## License

By contributing to CartMax, you agree that your contributions will be licensed under the same proprietary license as the project. See [LICENSE](LICENSE) for details.

---

**Thank you for contributing to CartMax! **

Your contributions help make CartMax better for everyone. We appreciate your time and effort!
