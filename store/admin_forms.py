from django import forms
from django.contrib.admin.widgets import AdminFileWidget
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Product, Category, Order, Review
from django.contrib.auth.models import User
from .context_processors import convert_price, get_exchange_rates



class EnhancedProductAdminForm(forms.ModelForm):
    """Enhanced product form with advanced pricing controls and validation"""
    
    # Manual dual currency pricing - admin sets both prices independently
    
    # Indian Rupee Pricing
    price_inr = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px; font-size: 16px; font-weight: bold; color: #ff6b35;',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        help_text="Price in Indian Rupees (₹) - Required"
    )
    
    original_price_inr = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px; font-size: 14px; color: #666;',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        help_text="Original INR price (for discounts)"
    )
    
    # US Dollar Pricing
    price_usd = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px; font-size: 16px; font-weight: bold; color: #007cba;',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        help_text="Price in US Dollars ($) - Required"
    )
    
    original_price_usd = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px; font-size: 14px; color: #666;',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        help_text="Original USD price (for discounts)"
    )
    
    # Dual currency discount calculators
    inr_discount_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput inr-discount',
            'style': 'width: 100px;',
            'step': '0.1',
            'min': '0',
            'max': '90',
            'placeholder': '0.0'
        }),
        help_text="Apply INR discount % (optional)"
    )
    
    usd_discount_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput usd-discount',
            'style': 'width: 100px;',
            'step': '0.1',
            'min': '0',
            'max': '90',
            'placeholder': '0.0'
        }),
        help_text="Apply USD discount % (optional)"
    )
    
    # Stock management with alerts
    stock = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'vIntegerField stock-input',
            'style': 'width: 100px; font-weight: bold;',
            'min': '0'
        }),
        help_text="Current stock quantity"
    )
    
    # Low stock threshold
    low_stock_alert = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vIntegerField',
            'style': 'width: 80px;',
            'min': '0'
        }),
        help_text="Alert when stock falls below this number"
    )
    
    # Enhanced description with character counter
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'vLargeTextField',
            'rows': 6,
            'cols': 80,
            'style': 'resize: vertical;',
            'maxlength': 2000
        }),
        help_text="Detailed product description (max 2000 characters)"
    )
    
    short_description = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'vTextField',
            'rows': 2,
            'cols': 80,
            'maxlength': 300
        }),
        help_text="Brief description for product listings (max 300 characters)"
    )
    
    # SEO fields with character limits
    meta_title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'vTextField',
            'style': 'width: 400px;',
            'maxlength': 200,
            'placeholder': 'SEO title for search engines'
        }),
        help_text="SEO title (max 200 characters)"
    )
    
    meta_description = forms.CharField(
        max_length=160,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'vTextField',
            'rows': 3,
            'cols': 60,
            'maxlength': 160,
            'placeholder': 'SEO description for search engines'
        }),
        help_text="SEO meta description (max 160 characters)"
    )
    
    # Slug management field
    slug = forms.SlugField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'vSlugField',
            'style': 'width: 400px;',
            'readonly': True,  # Read-only by default to prevent URL breakage
        }),
        help_text="Product URL slug (auto-generated). ⚠️ Changing this will break existing links!"
    )
    
    update_slug = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'vCheckboxInput update-slug-checkbox',
            'onchange': 'toggleSlugEditing()'
        }),
        label="Allow slug editing",
        help_text="⚠️ Warning: Changing the slug will make old links broken. Use only if necessary."
    )
    
    # Enhanced image upload with preview
    main_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        }),
        help_text="Main product image (recommended: 800x800px, max 5MB)"
    )
    
    class Meta:
        model = Product
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom CSS classes and enhance existing fields
        if 'category' in self.fields:
            self.fields['category'].widget.attrs.update({
                'class': 'vSelect',
                'style': 'width: 300px;'
            })
        
        if 'brand' in self.fields:
            self.fields['brand'].widget.attrs.update({
                'class': 'vTextField',
                'style': 'width: 200px;',
                'list': 'brand-suggestions'
            })
        
        # Initialize dual currency fields if editing existing product
        if self.instance and self.instance.pk:
            # Populate existing currency values
            if hasattr(self.instance, 'price_inr') and self.instance.price_inr:
                self.fields['price_inr'].initial = self.instance.price_inr
            if hasattr(self.instance, 'price_usd') and self.instance.price_usd:
                self.fields['price_usd'].initial = self.instance.price_usd
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Get dual currency values
        price_inr = cleaned_data.get('price_inr')
        price_usd = cleaned_data.get('price_usd')
        original_price_inr = cleaned_data.get('original_price_inr')
        original_price_usd = cleaned_data.get('original_price_usd')
        inr_discount_percent = cleaned_data.get('inr_discount_percent')
        usd_discount_percent = cleaned_data.get('usd_discount_percent')
        stock = cleaned_data.get('stock')
        low_stock_alert = cleaned_data.get('low_stock_alert')
        
        # Ensure both currency prices are provided and > 0
        if not price_inr or price_inr <= 0:
            raise ValidationError({
                'price_inr': 'INR price is required and must be greater than 0.'
            })
        
        if not price_usd or price_usd <= 0:
            raise ValidationError({
                'price_usd': 'USD price is required and must be greater than 0.'
            })
        
        # Validate INR price relationships
        if price_inr and original_price_inr:
            if original_price_inr <= price_inr:
                raise ValidationError({
                    'original_price_inr': 'Original INR price must be higher than current INR price for discounts.'
                })
        
        # Validate USD price relationships
        if price_usd and original_price_usd:
            if original_price_usd <= price_usd:
                raise ValidationError({
                    'original_price_usd': 'Original USD price must be higher than current USD price for discounts.'
                })
        
        # Apply INR discount if specified
        if inr_discount_percent and inr_discount_percent > 0:
            if not original_price_inr and price_inr:
                cleaned_data['original_price_inr'] = price_inr
                original_price_inr = price_inr
            
            if original_price_inr:
                discount_multiplier = 1 - (inr_discount_percent / 100)
                new_price_inr = original_price_inr * discount_multiplier
                cleaned_data['price_inr'] = new_price_inr.quantize(Decimal('0.01'))
        
        # Apply USD discount if specified
        if usd_discount_percent and usd_discount_percent > 0:
            if not original_price_usd and price_usd:
                cleaned_data['original_price_usd'] = price_usd
                original_price_usd = price_usd
            
            if original_price_usd:
                discount_multiplier = 1 - (usd_discount_percent / 100)
                new_price_usd = original_price_usd * discount_multiplier
                cleaned_data['price_usd'] = new_price_usd.quantize(Decimal('0.01'))
        
        # Validate stock alert threshold
        if stock is not None and low_stock_alert is not None:
            if low_stock_alert > stock:
                self.add_error('low_stock_alert', 'Low stock alert threshold cannot be higher than current stock.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Store additional data if needed
        # For now, low_stock_alert isn't in the model, but could be added later
        
        if commit:
            instance.save()
        
        return instance


class BulkPriceUpdateForm(forms.Form):
    """Form for bulk price updates"""
    
    UPDATE_TYPES = [
        ('percentage', 'Percentage Change (%)'),
        ('fixed', 'Fixed Amount (₹)'),
        ('set', 'Set Exact Price (₹)')
    ]
    
    update_type = forms.ChoiceField(
        choices=UPDATE_TYPES,
        widget=forms.RadioSelect(attrs={
            'class': 'radiolist'
        }),
        help_text="Choose how you want to update the prices"
    )
    
    value = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 200px; font-size: 16px;',
            'step': '0.01'
        }),
        help_text="Enter the value for price update"
    )
    
    update_original_price = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'vCheckboxInput'
        }),
        help_text="Update original price to current price before applying changes"
    )
    
    apply_to_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkboxselectmultiple'
        }),
        help_text="Limit updates to specific categories (optional)"
    )
    
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px;',
            'step': '0.01',
            'min': '0.01'
        }),
        help_text="Minimum price limit (prices won't go below this)"
    )
    
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px;',
            'step': '0.01'
        }),
        help_text="Maximum price limit (prices won't go above this)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price >= max_price:
            raise ValidationError("Minimum price must be less than maximum price.")
        
        return cleaned_data


class SmartPricingForm(forms.Form):
    """Form for smart pricing analysis and recommendations"""
    
    ANALYSIS_TYPES = [
        ('competitive', 'Competitive Analysis'),
        ('margin', 'Profit Margin Analysis'),
        ('demand', 'Demand-Based Pricing'),
        ('seasonal', 'Seasonal Pricing')
    ]
    
    analysis_type = forms.ChoiceField(
        choices=ANALYSIS_TYPES,
        widget=forms.Select(attrs={
            'class': 'vSelect',
            'style': 'width: 250px;'
        }),
        help_text="Select the type of pricing analysis"
    )
    
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkboxselectmultiple'
        }),
        help_text="Select categories to analyze (leave empty for all)"
    )
    
    price_range_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px;',
            'step': '0.01'
        }),
        help_text="Minimum price range for analysis"
    )
    
    price_range_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 150px;',
            'step': '0.01'
        }),
        help_text="Maximum price range for analysis"
    )
    
    include_out_of_stock = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'vCheckboxInput'
        }),
        help_text="Include out-of-stock products in analysis"
    )


class QuickDiscountForm(forms.Form):
    """Form for applying quick discounts"""
    
    discount_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'vNumberInput',
            'style': 'width: 100px; font-size: 16px;',
            'step': '0.1',
            'min': '0.1',
            'max': '90'
        }),
        help_text="Discount percentage to apply"
    )
    
    start_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'vDateTimeInput',
            'type': 'datetime-local'
        }),
        help_text="When the discount starts (leave empty for immediate)"
    )
    
    end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'vDateTimeInput',
            'type': 'datetime-local'
        }),
        help_text="When the discount ends (leave empty for permanent)"
    )
    
    reason = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'vTextField',
            'style': 'width: 300px;',
            'placeholder': 'e.g., Flash Sale, Clearance, Seasonal Offer'
        }),
        help_text="Reason for the discount (for record keeping)"
    )


class OrderManagementForm(forms.ModelForm):
    """Enhanced order management form with currency support"""
    
    class Meta:
        model = Order
        fields = ['status', 'total', 'shipping_amount', 'tax_amount', 'email', 'phone', 'address']
    
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'width: 200px;'
        }),
        help_text="Update order status"
    )
    
    total = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 150px;',
            'step': '0.01'
        }),
        help_text="Order total in current currency"
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add order notes...'
        }),
        help_text="Internal notes for this order"
    )
    
    def __init__(self, *args, **kwargs):
        self.currency = kwargs.pop('currency', 'INR')
        super().__init__(*args, **kwargs)
        
        # Update help text based on currency
        if self.currency == 'USD':
            self.fields['total'].help_text = "Order total in USD"
        else:
            self.fields['total'].help_text = "Order total in INR (₹)"


class ReviewModerationForm(forms.ModelForm):
    """Enhanced review moderation form"""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment', 'is_approved']
    
    rating = forms.ChoiceField(
        choices=Review.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        help_text="Product rating"
    )
    
    is_approved = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Approve this review for public display"
    )
    
    admin_response = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Optional response from admin...'
        }),
        help_text="Admin response to the review (visible to customers)"
    )
    
    moderation_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Internal moderation notes...'
        }),
        help_text="Internal notes (not visible to customers)"
    )


class CurrencyConversionForm(forms.Form):
    """Form for currency conversion operations in admin"""
    
    from_currency = forms.ChoiceField(
        choices=[('INR', 'Indian Rupee (₹)'), ('USD', 'US Dollar ($)')],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'width: 200px;'
        }),
        initial='INR'
    )
    
    to_currency = forms.ChoiceField(
        choices=[('INR', 'Indian Rupee (₹)'), ('USD', 'US Dollar ($)')],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'width: 200px;'
        }),
        initial='USD'
    )
    
    apply_to_products = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Convert product prices"
    )
    
    update_original_prices = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Also convert original prices (for discounts)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        from_currency = cleaned_data.get('from_currency')
        to_currency = cleaned_data.get('to_currency')
        
        if from_currency == to_currency:
            raise ValidationError("From and to currencies must be different.")
        
        return cleaned_data
    
    def get_conversion_rate(self):
        """Get current conversion rate"""
        rates = get_exchange_rates()
        from_currency = self.cleaned_data['from_currency']
        to_currency = self.cleaned_data['to_currency']
        
        if from_currency == 'USD' and to_currency == 'INR':
            return rates['USD_TO_INR']
        elif from_currency == 'INR' and to_currency == 'USD':
            return rates['INR_TO_USD']
        
        return Decimal('1')


class BulkProductOperationForm(forms.Form):
    """Form for bulk operations on products"""
    
    OPERATION_CHOICES = [
        ('activate', 'Activate Products'),
        ('deactivate', 'Deactivate Products'),
        ('update_category', 'Update Category'),
        ('apply_discount', 'Apply Discount'),
        ('update_stock', 'Update Stock'),
        ('convert_currency', 'Convert Currency')
    ]
    
    operation = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'width: 250px;'
        }),
        help_text="Select bulk operation to perform"
    )
    
    new_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'width: 200px;'
        }),
        help_text="New category (for category updates)"
    )
    
    discount_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px;',
            'min': '0',
            'max': '90',
            'step': '0.1'
        }),
        help_text="Discount percentage (for discount operations)"
    )
    
    stock_adjustment = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px;'
        }),
        help_text="Stock adjustment amount (+ to increase, - to decrease)"
    )
    
    target_currency = forms.ChoiceField(
        choices=[('INR', 'Indian Rupee (₹)'), ('USD', 'US Dollar ($)')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'width: 200px;'
        }),
        help_text="Target currency (for conversion operations)"
    )
    
    confirmation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="I confirm this bulk operation",
        help_text="You must confirm before proceeding with bulk operations"
    )
