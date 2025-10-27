from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class Category(models.Model):
    # just product categories
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # auto-generate slug if not set
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('store:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    # ecommerce products with dual pricing
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    # need both INR and USD prices
    price_inr = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price in INR"
    )
    price_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price in USD"
    )
    original_price_inr = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Original price in INR (for discount calculation)"
    )
    original_price_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Original price in USD (for discount calculation)"
    )
    
    # Backward compatibility fields - will be deprecated
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Search-related fields
    search_keywords = models.TextField(blank=True, help_text="Additional keywords for search (comma-separated)")
    meta_title = models.CharField(max_length=200, blank=True, help_text="SEO title for search engines")
    meta_description = models.TextField(blank=True, help_text="SEO description for search engines")
    
    # Product attributes for filtering
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, blank=True, help_text="Dimensions (L x W x H)")
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    
    # Business fields
    min_order_quantity = models.PositiveIntegerField(default=1)
    is_digital = models.BooleanField(default=False, help_text="Is this a digital product?")
    is_returnable = models.BooleanField(default=True)
    warranty_period = models.CharField(max_length=100, blank=True, help_text="e.g., '1 year', '6 months'")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['available']),
            models.Index(fields=['featured']),
            models.Index(fields=['price']),
            models.Index(fields=['brand']),
            models.Index(fields=['category', 'available']),
            models.Index(fields=['available', 'stock']),
            models.Index(fields=['created_at']),
            models.Index(fields=['color']),
            models.Index(fields=['size']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Only generate slug for new products, preserve existing slugs to prevent URL breakage
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"AMZ-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})
    
    def get_price(self, currency='INR'):
        # get price in the right currency
        if currency.upper() == 'USD':
            return self.price_usd
        return self.price_inr
    
    def get_original_price(self, currency='INR'):
        # original price before discount
        if currency.upper() == 'USD':
            return self.original_price_usd
        return self.original_price_inr
    
    def get_discount_percentage(self, currency='INR'):
        # calc discount %
        current_price = self.get_price(currency)
        original_price = self.get_original_price(currency)
        
        if original_price and original_price > current_price:
            return int(((original_price - current_price) / original_price) * 100)
        return 0
    
    def get_savings_amount(self, currency='INR'):
        # how much user saves
        current_price = self.get_price(currency)
        original_price = self.get_original_price(currency)
        
        if original_price and original_price > current_price:
            return original_price - current_price
        return 0
    
    def has_discount(self, currency='INR'):
        # is this product on sale?
        return self.get_discount_percentage(currency) > 0
    
    def get_average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    def get_review_count(self):
        return self.reviews.filter(is_approved=True).count()
    
    def is_in_stock(self):
        return self.available and self.stock > 0


class ProductSlug(models.Model):
    """Track old product slugs for URL redirection"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='old_slugs')
    slug = models.SlugField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'slug']
    
    def __str__(self):
        return f"{self.product.name} - {self.slug}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image"


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ['product', 'name']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.user.username}"


class UserProfile(models.Model):
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee (₹)'),
        ('USD', 'US Dollar ($)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address_line_1 = models.CharField(max_length=200, blank=True)
    address_line_2 = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=200, blank=True)  # Single address field for compatibility
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='United States')
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Currency preference (NEW)
    preferred_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_currency_symbol(self):
        """Get currency symbol for user's preferred currency"""
        return '₹' if self.preferred_currency == 'INR' else '$'
    
    def get_full_address(self):
        address_parts = [self.address_line_1, self.address_line_2, self.city, self.state, self.postal_code]
        return ', '.join(filter(None, address_parts))


class Cart(models.Model):
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee (₹)'),
        ('USD', 'US Dollar ($)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
    # Coupon support
    applied_coupon = models.ForeignKey(
        'DiscountCoupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts'
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart ({self.session_key[:8]}...)"
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_tax(self):
        return self.get_total_price() * Decimal('0.08')  # 8% tax
    
    def get_final_total(self):
        return self.get_total_price() + self.get_tax()
    
    def get_total_price_in_currency(self, currency='USD'):
        """Get total price in specified currency"""
        # If currency not specified or empty, use cart's currency
        if not currency:
            currency = self.currency or 'USD'
        return sum(item.get_total_price_in_currency(currency) for item in self.items.all())
    
    def get_tax_in_currency(self, currency='USD'):
        """Get tax amount in specified currency"""
        return self.get_total_price_in_currency(currency) * Decimal('0.08')
    
    def get_final_total_in_currency(self, currency='USD'):
        """Get final total (including tax) in specified currency"""
        return self.get_total_price_in_currency(currency) + self.get_tax_in_currency(currency)
    
    def get_currency_symbol(self):
        """Get the currency symbol for this cart's currency"""
        return '₹' if self.currency == 'INR' else '$'
    
    def calculate_discount(self):
        """Calculate and update discount amount based on applied coupon"""
        if self.applied_coupon:
            subtotal = self.get_total_price_in_currency(self.currency)
            self.discount_amount = self.applied_coupon.calculate_discount(subtotal)
        else:
            self.discount_amount = Decimal('0')
        return self.discount_amount
    
    def get_discounted_total(self, currency=None):
        """Get total after applying discount in specified currency"""
        if currency is None:
            currency = self.currency
        total = self.get_total_price_in_currency(currency)
        return total - self.discount_amount


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    # Dual currency price snapshot (captured at time of adding to cart)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_inr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Backward compatibility field - deprecated
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total_price(self):
        # Backward compatibility - use price_usd as fallback
        return self.quantity * (self.price_usd or self.price or Decimal('0'))
    
    def get_total(self):
        """Get total price - for backward compatibility, uses USD"""
        return self.get_total_price_in_currency('USD')
    
    def get_total_price_in_currency(self, currency='USD'):
        """Get total price of this item (quantity * price) in specified currency
        
        Uses stored snapshot prices captured at time of adding to cart.
        This prevents price corruption when product prices change or when switching currencies.
        """
        if currency.upper() == 'INR':
            unit_price = self.price_inr
            # Fallback: if INR price not set, try to get from product
            if not unit_price:
                unit_price = self.product.price_inr or Decimal('0')
        else:
            unit_price = self.price_usd
            # Fallback: if USD price not set, try to get from product
            if not unit_price:
                unit_price = self.product.price_usd or Decimal('0')
        
        if unit_price:
            return self.quantity * unit_price
        return Decimal('0')
    
    def save(self, *args, **kwargs):
        # Capture dual-currency price snapshot at time of adding to cart
        # Always ensure both prices are set from product
        if not self.price_usd:
            self.price_usd = self.product.price_usd or Decimal('0')
        if not self.price_inr:
            self.price_inr = self.product.price_inr or Decimal('0')
        
        # Maintain backward compatibility
        if not self.price:
            self.price = self.price_usd or self.price_inr or self.product.price
        
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('cartmax_pay', 'CartMax Wallet'),
    ]
    
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee (₹)'),
        ('USD', 'US Dollar ($)'),
    ]
    
    order_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Customer Information
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='US', blank=True)
    
    # Order Details
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='credit_card')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
    # Coupon support
    applied_coupon = models.ForeignKey(
        'DiscountCoupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Legacy fields (keeping for compatibility)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_name = models.CharField(max_length=200, blank=True)
    shipping_address_line_1 = models.CharField(max_length=200, blank=True)
    shipping_address_line_2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_id} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"AMZ{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_subtotal(self):
        """Get subtotal before discount in this order's currency"""
        if self.original_subtotal:
            return self.original_subtotal
        return sum(item.get_total_price_in_currency(self.currency) for item in self.items.all())
    
    def get_discount_amount(self):
        """Get discount amount for this order"""
        return self.discount_amount or Decimal('0')
    
    def get_discounted_subtotal(self):
        """Get subtotal after discount"""
        return self.get_subtotal() - self.get_discount_amount()
    
    def get_tax(self):
        """Get tax amount in this order's currency (calculated on FULL subtotal, not discounted)"""
        if self.tax_amount:
            return self.tax_amount
        # CRITICAL: Tax is calculated on FULL subtotal (before discount)
        full_subtotal = self.get_subtotal()
        return full_subtotal * Decimal('0.08')  # 8% tax on full amount
    
    def get_final_total(self):
        """Calculate final total: (subtotal - discount) + tax + shipping"""
        return self.get_discounted_subtotal() + self.get_tax() + self.shipping_amount
    
    @property
    def order_number(self):
        """Return order number for display"""
        return self.order_id
    
    @property
    def total_amount(self):
        """Return total amount for compatibility"""
        return self.total or self.get_final_total()
    
    def get_shipping_address(self):
        if self.address:  # New format
            return f"{self.address}, {self.city}, {self.postal_code}, {self.country}"
        # Legacy format
        address_parts = [
            self.shipping_address_line_1,
            self.shipping_address_line_2,
            self.shipping_city,
            self.shipping_state,
            self.shipping_postal_code,
            self.shipping_country
        ]
        return ', '.join(filter(None, address_parts))
    
    def get_currency_symbol(self):
        """Get the currency symbol for this order's currency"""
        return '₹' if self.currency == 'INR' else '$'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # Dual currency price snapshot (captured at time of order creation)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_inr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Backward compatibility field - deprecated
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order: {self.order.order_id})"
    
    def get_total_price(self):
        # Backward compatibility - use price_usd as fallback
        return self.quantity * (self.price_usd or self.price or Decimal('0'))
    
    def get_total_price_in_currency(self, currency='USD'):
        """Get total price of this order item in specified currency
        
        Uses stored snapshot prices captured at time of order creation.
        """
        if currency.upper() == 'INR':
            unit_price = self.price_inr or Decimal('0')
        else:
            unit_price = self.price_usd or Decimal('0')
        
        if unit_price:
            return self.quantity * unit_price
        return Decimal('0')
    
    def get_total(self):
        return self.get_total_price()


class Wishlist(models.Model):
    """User's wishlist to save favorite products - supports both authenticated and guest users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='wishlists')
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="Session key for guest users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'session_key']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.user.username}'s Wishlist"
        return f"Guest Wishlist ({self.session_key[:8]}...)"
    
    def get_item_count(self):
        return self.items.count()
    
    def has_product(self, product):
        return self.items.filter(product=product).exists()
    
    @staticmethod
    def get_for_request(request):
        """Get or create wishlist for either authenticated user or guest session"""
        if request.user.is_authenticated:
            wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            wishlist, created = Wishlist.objects.get_or_create(session_key=request.session.session_key)
        return wishlist


class WishlistItem(models.Model):
    """Individual items in user's wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['wishlist', 'product']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"


class ProductRecommendation(models.Model):
    """Product recommendations based on different algorithms"""
    RECOMMENDATION_TYPES = [
        ('similar', 'Similar Products'),
        ('frequently_bought', 'Frequently Bought Together'),
        ('popular', 'Popular Products'),
        ('user_based', 'Recommended for You'),
        ('trending', 'Trending Now'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations')
    recommended_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommended_for')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    score = models.FloatField(default=0.0, help_text='Recommendation strength (0.0-1.0)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'recommended_product', 'recommendation_type']
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"{self.recommended_product.name} recommended for {self.product.name} ({self.recommendation_type})"


class UserProductInteraction(models.Model):
    """Track user interactions with products for personalized recommendations"""
    INTERACTION_TYPES = [
        ('view', 'Product View'),
        ('cart', 'Added to Cart'),
        ('purchase', 'Purchase'),
        ('wishlist', 'Added to Wishlist'),
        ('review', 'Left a Review'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_interactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    interaction_count = models.PositiveIntegerField(default=1)
    last_interaction = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product', 'interaction_type']
        ordering = ['-last_interaction']
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.product.name}"


class ProductComparison(models.Model):
    """Store user's product comparisons"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='comparisons')
    session_key = models.CharField(max_length=255, blank=True, null=True, help_text='For anonymous users')
    name = models.CharField(max_length=200, default='Product Comparison')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        username = self.user.username if self.user else f'Anonymous ({self.session_key[:8]}...)'
        return f"{self.name} by {username}"
    
    def get_product_count(self):
        return self.items.count()
    
    def can_add_more(self):
        return self.get_product_count() < 4  # Maximum 4 products for comparison


class ComparisonItem(models.Model):
    """Individual products in a comparison"""
    comparison = models.ForeignKey(ProductComparison, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comparison', 'product']
        ordering = ['added_at']
    
    def __str__(self):
        return f"{self.product.name} in comparison"


class InventoryMovement(models.Model):
    """Track all inventory movements (stock changes)"""
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase/Restock'),
        ('sale', 'Sale'),
        ('adjustment', 'Manual Adjustment'),
        ('return', 'Customer Return'),
        ('damage', 'Damaged/Lost'),
        ('transfer', 'Transfer'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField(help_text='Positive for stock increase, negative for decrease')
    stock_before = models.PositiveIntegerField(help_text='Stock level before this movement')
    stock_after = models.PositiveIntegerField(help_text='Stock level after this movement')
    reference_number = models.CharField(max_length=100, blank=True, help_text='Order ID, Invoice number, etc.')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity_change:+d})"


class LowStockAlert(models.Model):
    """Track low stock alerts for products"""
    ALERT_LEVELS = [
        ('low', 'Low Stock'),
        ('critical', 'Critical Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts')
    alert_level = models.CharField(max_length=20, choices=ALERT_LEVELS)
    threshold = models.PositiveIntegerField(help_text='Stock level that triggered this alert')
    current_stock = models.PositiveIntegerField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'alert_level']
    
    def __str__(self):
        status = 'Resolved' if self.is_resolved else 'Active'
        return f"{self.product.name} - {self.get_alert_level_display()} ({status})"
    
    def resolve_alert(self):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()


class InventorySettings(models.Model):
    """Global inventory management settings"""
    low_stock_threshold = models.PositiveIntegerField(default=10, help_text='Default low stock threshold')
    critical_stock_threshold = models.PositiveIntegerField(default=5, help_text='Default critical stock threshold')
    auto_create_alerts = models.BooleanField(default=True, help_text='Automatically create stock alerts')
    email_alerts = models.BooleanField(default=True, help_text='Send email alerts for low stock')
    alert_frequency_hours = models.PositiveIntegerField(default=24, help_text='Hours between repeated alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Inventory Settings'
        verbose_name_plural = 'Inventory Settings'
    
    def __str__(self):
        return f"Inventory Settings (Low: {self.low_stock_threshold}, Critical: {self.critical_stock_threshold})"


# ============================================================================
# CUSTOM ADMIN MODELS - THE FOUNDATION OF POWER!
# ============================================================================

class AdminRole(models.Model):
    """Admin roles for hierarchical access control"""
    ROLE_CHOICES = [
        ('supreme_admin', '👑 Supreme Admin - Controls Everything'),
        ('product_manager', '📦 Product Manager - Catalog Control'), 
        ('order_manager', '📋 Order Manager - Fulfillment Control'),
        ('customer_service', '👥 Customer Service - User Support'),
        ('analyst', '📊 Analyst - Reports & Analytics'),
        ('moderator', '🛡️ Moderator - Content Control'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    permissions = models.JSONField(default=dict, help_text="Custom permissions JSON")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Admin Role'
        verbose_name_plural = 'Admin Roles'


class AdminProfile(models.Model):
    """Extended profile for admin users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.ForeignKey(AdminRole, on_delete=models.SET_NULL, null=True, blank=True)
    avatar = models.ImageField(upload_to='admin_avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True, help_text="Admin bio/description")
    
    # Preferences
    theme_preference = models.CharField(
        max_length=10, 
        choices=[('light', 'Light Theme'), ('dark', 'Dark Theme')], 
        default='dark'
    )
    dashboard_layout = models.JSONField(default=dict, help_text="Dashboard widget preferences")
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    allowed_ip_addresses = models.TextField(blank=True, help_text="Comma-separated IP addresses")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role.display_name if self.role else 'No Role'}"
    
    def has_permission(self, permission_name):
        """Check if admin has specific permission"""
        if not self.role:
            return False
        if self.role.name == 'supreme_admin':
            return True  # Supreme admin has all permissions
        return self.role.permissions.get(permission_name, False)
    
    def get_dashboard_widgets(self):
        """Get user's preferred dashboard widgets"""
        default_widgets = {
            'analytics': True,
            'recent_orders': True,
            'top_products': True,
            'user_activity': True,
            'revenue_chart': True
        }
        return self.dashboard_layout.get('widgets', default_widgets)
    
    class Meta:
        verbose_name = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'


class AdminActivity(models.Model):
    """Log all admin activities for audit trail"""
    ACTION_TYPES = [
        ('login', '🔐 Login'),
        ('logout', '🚪 Logout'),
        ('create', '➕ Create'),
        ('update', '✏️ Update'),
        ('delete', '🗑️ Delete'),
        ('bulk_action', '🔄 Bulk Action'),
        ('export', '📤 Export'),
        ('import', '📥 Import'),
        ('email_blast', '📧 Email Blast'),
        ('maintenance', '🔧 Maintenance'),
        ('config_change', '⚙️ Config Change'),
        ('security_action', '🛡️ Security Action'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    object_type = models.CharField(max_length=100, blank=True, help_text="Model name affected")
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True, help_text="String representation")
    
    # Technical details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    additional_data = models.JSONField(default=dict, help_text="Extra data about the action")
    
    # Results
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.get_action_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Activity'
        verbose_name_plural = 'Admin Activities'
        indexes = [
            models.Index(fields=['admin_user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]


class SiteConfiguration(models.Model):
    """Site-wide configuration that admins can control"""
    key = models.CharField(max_length=100, unique=True, help_text="Configuration key")
    value = models.TextField(help_text="Configuration value (JSON for complex data)")
    description = models.CharField(max_length=200, help_text="Human-readable description")
    category = models.CharField(max_length=50, default='general', help_text="Configuration category")
    is_secret = models.BooleanField(default=False, help_text="Hide value in admin (passwords, keys)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.key} = {'***' if self.is_secret else self.value[:50]}"
    
    class Meta:
        ordering = ['category', 'key']
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configurations'


class AdminAnnouncement(models.Model):
    """Site-wide announcements that admins can create"""
    ANNOUNCEMENT_TYPES = [
        ('info', 'ℹ️ Information'),
        ('warning', '⚠️ Warning'),
        ('success', '✅ Success'),
        ('error', '❌ Error'),
        ('maintenance', '🔧 Maintenance'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='info')
    
    # Display settings
    is_active = models.BooleanField(default=True)
    show_to_users = models.BooleanField(default=True, help_text="Show to regular users")
    show_to_admins = models.BooleanField(default=True, help_text="Show to admin users")
    is_dismissible = models.BooleanField(default=True, help_text="Can users dismiss this?")
    
    # Scheduling
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_announcement_type_display()})"
    
    def is_currently_active(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Announcement'
        verbose_name_plural = 'Admin Announcements'


# ============================================================================
# ENHANCED SITE-WIDE ANNOUNCEMENT SYSTEM - Phase 2A Final Feature
# ============================================================================

class SiteAnnouncement(models.Model):
    """Enhanced site-wide announcements with advanced features"""
    ANNOUNCEMENT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Critical Alert'),
        ('promotion', 'Promotion'),
        ('maintenance', 'Maintenance'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    TARGET_AUDIENCES = [
        ('all', 'All Users'),
        ('registered', 'Registered Users Only'),
        ('guests', 'Guest Users Only'),
        ('staff', 'Staff Only'),
        ('premium', 'Premium Users'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='info')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCES, default='all')
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Display options
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True)
    show_on_homepage = models.BooleanField(default=True)
    show_in_header = models.BooleanField(default=False)
    show_as_popup = models.BooleanField(default=False)
    
    # Action buttons
    action_button_text = models.CharField(max_length=50, blank=True, null=True)
    action_button_url = models.URLField(blank=True, null=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    clicks_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Site Announcement'
        verbose_name_plural = 'Site Announcements'
    
    def __str__(self):
        return f"{self.title} ({self.announcement_type})"
    
    def is_currently_active(self):
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.start_date > now:
            return False
        
        if self.end_date and self.end_date < now:
            return False
        
        return True
    
    def get_css_class(self):
        type_classes = {
            'info': 'alert-info',
            'warning': 'alert-warning', 
            'success': 'alert-success',
            'danger': 'alert-danger',
            'promotion': 'alert-primary',
            'maintenance': 'alert-secondary',
        }
        return type_classes.get(self.announcement_type, 'alert-info')
    
    def get_icon(self):
        type_icons = {
            'info': 'fas fa-info-circle',
            'warning': 'fas fa-exclamation-triangle',
            'success': 'fas fa-check-circle', 
            'danger': 'fas fa-exclamation-circle',
            'promotion': 'fas fa-star',
            'maintenance': 'fas fa-tools',
        }
        return type_icons.get(self.announcement_type, 'fas fa-info-circle')


class AnnouncementView(models.Model):
    """Track who viewed each announcement"""
    announcement = models.ForeignKey(SiteAnnouncement, on_delete=models.CASCADE, related_name='announcement_views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'user', 'ip_address']
        verbose_name = 'Announcement View'
        verbose_name_plural = 'Announcement Views'
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{self.announcement.title} - {user_str}"


class AnnouncementDismissal(models.Model):
    """Track who dismissed each announcement"""
    announcement = models.ForeignKey(SiteAnnouncement, on_delete=models.CASCADE, related_name='dismissals')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    dismissed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'user', 'ip_address']
        verbose_name = 'Announcement Dismissal'
        verbose_name_plural = 'Announcement Dismissals'
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{self.announcement.title} dismissed by {user_str}"


# ==================== SEARCH & TAG MODELS ====================

class ProductTag(models.Model):
    """Tags for products to improve search and categorization"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code for tag display')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Product Tag'
        verbose_name_plural = 'Product Tags'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductTagAssignment(models.Model):
    """Many-to-many relationship between products and tags"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='tag_assignments')
    tag = models.ForeignKey(ProductTag, on_delete=models.CASCADE, related_name='product_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['product', 'tag']
        ordering = ['tag__name']
        verbose_name = 'Product Tag Assignment'
        verbose_name_plural = 'Product Tag Assignments'
    
    def __str__(self):
        return f"{self.product.name} - {self.tag.name}"


class SearchQuery(models.Model):
    """Track search queries for analytics and improvements"""
    query = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Search context
    category_filter = models.CharField(max_length=100, blank=True)
    price_filter = models.CharField(max_length=50, blank=True)
    brand_filter = models.CharField(max_length=100, blank=True)
    sort_by = models.CharField(max_length=50, blank=True)
    
    # Results
    results_count = models.PositiveIntegerField(default=0)
    clicked_products = models.ManyToManyField(Product, blank=True, through='SearchProductClick')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Search Query'
        verbose_name_plural = 'Search Queries'
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['created_at']),
            models.Index(fields=['results_count']),
        ]
    
    def __str__(self):
        return f"'{self.query}' ({self.results_count} results)"


class SearchProductClick(models.Model):
    """Track which products were clicked from search results"""
    search_query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name='product_clicks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='search_clicks')
    click_position = models.PositiveIntegerField(help_text='Position in search results (1-based)')
    clicked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['search_query', 'product']
        ordering = ['click_position']
        verbose_name = 'Search Product Click'
        verbose_name_plural = 'Search Product Clicks'
    
    def __str__(self):
        return f"{self.search_query.query} -> {self.product.name}"


class PopularSearch(models.Model):
    """Cache popular search terms for suggestions"""
    query = models.CharField(max_length=255, unique=True, db_index=True)
    search_count = models.PositiveIntegerField(default=0)
    last_searched = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-search_count', '-last_searched']
        verbose_name = 'Popular Search'
        verbose_name_plural = 'Popular Searches'
    
    def __str__(self):
        return f"'{self.query}' ({self.search_count} searches)"


# ==================== DISCOUNT COUPON SYSTEM ====================

class DiscountCoupon(models.Model):
    """Discount coupons that can be applied to orders"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage (%)'),
        ('fixed_amount', 'Fixed Amount'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('INR', 'Indian Rupee (₹)'),
        ('both', 'Both USD & INR'),
    ]
    
    coupon_code = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        help_text="Unique code users will enter (e.g., SAVE10)"
    )
    description = models.TextField(blank=True, help_text="Internal description of this coupon")
    
    # Discount details
    discount_type = models.CharField(
        max_length=20, 
        choices=DISCOUNT_TYPE_CHOICES, 
        default='percentage',
        help_text="Type of discount: percentage or fixed amount"
    )
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Discount value (percentage 0-100 or fixed amount)"
    )
    
    # Order conditions
    minimum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Minimum order amount required to use this coupon"
    )
    maximum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Maximum order amount this coupon is valid for (null = no limit)"
    )
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of times this coupon has been used"
    )
    max_usage_limit = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Maximum total uses allowed (null = unlimited)"
    )
    
    # Validity
    is_active = models.BooleanField(default=True, help_text="Enable/disable this coupon")
    expiration_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this coupon expires (null = no expiration)"
    )
    
    # Currency support
    applicable_currencies = models.CharField(
        max_length=20,
        choices=CURRENCY_CHOICES,
        default='both',
        help_text="Which currencies this coupon is valid for"
    )
    # Currency of min/max amounts - defaults to USD for backward compatibility
    amount_currency = models.CharField(
        max_length=20,
        choices=[('USD', 'US Dollar ($)'), ('INR', 'Indian Rupee (₹)')],
        default='USD',
        help_text="Currency in which minimum and maximum order amounts are specified"
    )
    
    # Tracking
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_coupons',
        help_text="Admin user who created this coupon"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Discount Coupon'
        verbose_name_plural = 'Discount Coupons'
        indexes = [
            models.Index(fields=['coupon_code']),
            models.Index(fields=['is_active', 'expiration_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.coupon_code} - {self.get_discount_type_display()}"
    
    def is_valid(self):
        """Check if coupon is active, not expired, and under usage limit"""
        from django.utils import timezone
        
        if not self.is_active:
            return False
        
        if self.expiration_date and timezone.now() > self.expiration_date:
            return False
        
        if self.max_usage_limit and self.usage_count >= self.max_usage_limit:
            return False
        
        return True
    
    def can_be_applied(self, order_amount, currency='USD'):
        """Check if this coupon can be applied to an order with given amount and currency"""
        if not self.is_valid():
            return False, "This coupon is no longer valid."
        
        # Check currency
        if self.applicable_currencies != 'both':
            if currency.upper() != self.applicable_currencies:
                return False, f"This coupon is not available for {currency}."
        
        # Check minimum order amount
        if self.minimum_order_amount and order_amount < self.minimum_order_amount:
            return False, f"This coupon requires a minimum order of {self.minimum_order_amount}."
        
        # Check maximum order amount
        if self.maximum_order_amount and order_amount > self.maximum_order_amount:
            return False, f"This coupon is only valid for orders up to {self.maximum_order_amount}."
        
        return True, "Valid"
    
    def calculate_discount(self, subtotal):
        """Calculate discount amount based on coupon type and subtotal"""
        if self.discount_type == 'percentage':
            discount = subtotal * (self.discount_value / Decimal('100'))
        else:  # fixed_amount
            discount = self.discount_value
        
        # Ensure discount doesn't exceed subtotal
        if discount > subtotal:
            discount = subtotal
        
        return discount
    
    def get_discount_display(self, subtotal=None):
        """Get a readable display of the discount"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        else:
            return f"{self.discount_value} off"
    
    def get_currency_symbol(self):
        """Get currency symbol for display (coupon amounts are stored in USD)"""
        return '$'  # Coupon amounts are always stored in USD


class CouponUsage(models.Model):
    """Track coupon usage per user to enforce per-user limits"""
    coupon = models.ForeignKey(
        DiscountCoupon, 
        on_delete=models.CASCADE, 
        related_name='user_usages'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='coupon_usages'
    )
    usage_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of times this user has used this coupon"
    )
    last_used_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['coupon', 'user']
        ordering = ['-last_used_at']
        verbose_name = 'Coupon Usage'
        verbose_name_plural = 'Coupon Usages'
        indexes = [
            models.Index(fields=['user', '-last_used_at']),
            models.Index(fields=['coupon', '-last_used_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} used {self.coupon.coupon_code} {self.usage_count} times"
    
    def can_use(self, max_per_user=1):
        """Check if user can use this coupon again (per-user limit)"""
        return self.usage_count < max_per_user
    
    def increment_usage(self):
        """Increment usage count when coupon is used"""
        self.usage_count += 1
        self.save()
        return self.usage_count
