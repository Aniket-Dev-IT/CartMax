from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from decimal import Decimal
import csv
from .models import *
from .emails import send_order_status_update_email
from .admin_forms import EnhancedProductAdminForm


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 3


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'price_display', 'discount_display', 'stock', 'stock_status', 
                   'available', 'featured', 'last_restock', 'profit_margin']
    list_filter = ['available', 'featured', 'category', 'brand', 'created_at', 'is_digital', 'is_returnable']
    search_fields = ['name', 'description', 'brand', 'sku', 'search_keywords']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductSpecificationInline, ProductImageInline]
    actions = ['mark_as_featured', 'mark_as_available', 'bulk_stock_update', 'generate_restock_report',
               'bulk_price_update', 'bulk_discount_apply', 'copy_prices_to_usd', 'smart_pricing_analysis']
    form = EnhancedProductAdminForm
    
    # Enhanced fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description', 'category', 'brand', 'sku')
        }),
        ('Pricing & Discounts', {
            'fields': (('price_currency', 'price', 'original_price'), ('quick_discount_percent',)),
            'classes': ('wide',),
            'description': 'Set pricing information and apply quick discounts. Currency selection prepares for multi-currency support.'
        }),
        ('Product Attributes', {
            'fields': ('weight', 'dimensions', 'color', 'size', 'material', 'warranty_period'),
            'classes': ('collapse',)
        }),
        ('Inventory & Business', {
            'fields': (('stock', 'low_stock_alert'), 'min_order_quantity', ('available', 'featured'), ('is_digital', 'is_returnable')),
            'classes': ('wide',),
            'description': 'Manage stock levels and business settings. Low stock alerts help with inventory management.'
        }),
        ('SEO & Search', {
            'fields': ('search_keywords', 'meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('main_image',),
        })
    )
    
    def price_display(self, obj):
        """Enhanced price display with currency and discount info - Shows BOTH INR and USD"""
        # Display INR pricing
        inr_price = obj.price_inr or obj.price  # Fallback to legacy field
        inr_discount = obj.get_discount_percentage('INR') if obj.price_inr else 0
        
        # Display USD pricing
        usd_price = obj.price_usd
        usd_discount = obj.get_discount_percentage('USD') if obj.price_usd else 0
        
        parts = []
        
        # INR section
        if inr_price:
            if obj.original_price_inr and obj.original_price_inr > inr_price and inr_discount > 0:
                inr_html = f'₹{inr_price} <span style="color: #d73527; font-weight: bold;">({inr_discount}% OFF)</span><br/><small style="color: #999; text-decoration: line-through;">₹{obj.original_price_inr}</small>'
            else:
                inr_html = f'₹{inr_price}'
            parts.append(inr_html)
        
        # USD section
        if usd_price:
            if obj.original_price_usd and obj.original_price_usd > usd_price and usd_discount > 0:
                usd_html = f'${usd_price} <span style="color: #d73527; font-weight: bold;">({usd_discount}% OFF)</span><br/><small style="color: #999; text-decoration: line-through;">${obj.original_price_usd}</small>'
            else:
                usd_html = f'${usd_price}'
            parts.append(usd_html)
        
        # Combine all parts with line breaks
        if parts:
            combined = '<br/>'.join(parts)
            return format_html(combined)
        else:
            return format_html('<span style="color: #999;">No price set</span>')
    price_display.short_description = 'Price (INR / USD)'
    
    def discount_display(self, obj):
        """Show discount information"""
        discount = obj.get_discount_percentage()
        if discount > 0:
            savings = obj.get_savings_amount()
            return format_html(
                '<span style="color: #d73527; font-weight: bold;">{discount}%</span><br/>'
                '<small style="color: #666;">Save ₹{savings}</small>',
                discount=discount, savings=savings
            )
        return format_html('<span style="color: #999;">No discount</span>')
    discount_display.short_description = 'Discount'
    
    def profit_margin(self, obj):
        """Calculate and display estimated profit margin"""
        # Assuming 30% markup as base cost (this can be customized)
        estimated_cost = obj.price * Decimal('0.70')
        if obj.price > 0:
            profit = obj.price - estimated_cost
            margin = float((profit / obj.price) * 100)
            color = '#28a745' if margin > 20 else '#ffc107' if margin > 10 else '#dc3545'
            return format_html(
                '<span style="color: {};">~{}%</span>',
                color,
                round(margin, 1)
            )
        return format_html('<span style="color: #999;">N/A</span>')
    profit_margin.short_description = 'Est. Margin'
    
    def stock_status(self, obj):
        from .inventory import inventory_manager
        settings = inventory_manager.get_settings()
        
        if obj.stock == 0:
            return format_html('<span style="color: red; font-weight: bold;">OUT OF STOCK</span>')
        elif obj.stock <= settings.critical_stock_threshold:
            return format_html('<span style="color: red;">CRITICAL</span>')
        elif obj.stock <= settings.low_stock_threshold:
            return format_html('<span style="color: orange;">LOW</span>')
        else:
            return format_html('<span style="color: green;">OK</span>')
    stock_status.short_description = 'Stock Status'
    
    def last_restock(self, obj):
        last_movement = obj.inventory_movements.filter(
            movement_type__in=['purchase', 'adjustment'],
            quantity_change__gt=0
        ).first()
        return last_movement.created_at.strftime('%Y-%m-%d') if last_movement else 'Never'
    last_restock.short_description = 'Last Restock'
    
    def mark_as_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f'{queryset.count()} products marked as featured.')
    mark_as_featured.short_description = 'Mark selected products as featured'
    
    def mark_as_available(self, request, queryset):
        queryset.update(available=True)
        self.message_user(request, f'{queryset.count()} products marked as available.')
    mark_as_available.short_description = 'Mark as available'
    
    def bulk_stock_update(self, request, queryset):
        if 'apply' in request.POST:
            stock_change = request.POST.get('stock_change', 0)
            try:
                stock_change = int(stock_change)
                from .inventory import inventory_manager
                
                updated_count = 0
                for product in queryset:
                    inventory_manager.update_stock(
                        product=product,
                        quantity_change=stock_change,
                        movement_type='adjustment',
                        notes=f'Bulk update by {request.user.username}',
                        created_by=request.user
                    )
                    updated_count += 1
                
                self.message_user(request, f'Updated stock for {updated_count} products.')
                return
            except ValueError:
                self.message_user(request, 'Invalid stock change value.', level=messages.ERROR)
        
        return render(request, 'admin/bulk_stock_update.html', {
            'products': queryset,
            'title': 'Bulk Stock Update'
        })
    bulk_stock_update.short_description = 'Bulk update stock levels'
    
    def generate_restock_report(self, request, queryset):
        from .inventory import inventory_manager
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="restock_suggestions.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Product', 'Current Stock', 'Daily Velocity', 'Days of Supply', 
                        'Suggested Restock', 'Priority'])
        
        for product in queryset:
            suggestion = inventory_manager.restock_suggestion(product)
            priority = 'High' if product.stock <= 5 else 'Medium' if product.stock <= 10 else 'Low'
            
            writer.writerow([
                product.name,
                suggestion['current_stock'],
                suggestion['daily_velocity'],
                suggestion['days_of_supply_current'],
                suggestion['suggested_restock'],
                priority
            ])
        
        return response
    generate_restock_report.short_description = 'Generate restock suggestions'
    
    def bulk_price_update(self, request, queryset):
        """Bulk update prices with percentage increase/decrease"""
        if 'apply' in request.POST:
            price_change_type = request.POST.get('price_change_type', 'percentage')
            price_change_value = request.POST.get('price_change_value', 0)
            update_original = request.POST.get('update_original', False)
            
            try:
                price_change_value = float(price_change_value)
                updated_count = 0
                
                for product in queryset:
                    old_price = product.price
                    
                    if price_change_type == 'percentage':
                        # Percentage increase/decrease
                        new_price = old_price * (1 + price_change_value / 100)
                    else:
                        # Fixed amount increase/decrease
                        new_price = old_price + Decimal(str(price_change_value))
                    
                    # Ensure price doesn't go below 0
                    new_price = max(Decimal('0.01'), Decimal(str(new_price)))
                    
                    product.price = new_price.quantize(Decimal('0.01'))
                    
                    # Update original price if requested
                    if update_original and not product.original_price:
                        product.original_price = old_price
                    
                    product.save()
                    updated_count += 1
                
                self.message_user(request, f'Updated prices for {updated_count} products.')
                return
            except (ValueError, TypeError):
                self.message_user(request, 'Invalid price change value.', level=messages.ERROR)
        
        return render(request, 'admin/bulk_price_update.html', {
            'products': queryset,
            'title': 'Bulk Price Update'
        })
    bulk_price_update.short_description = 'Bulk update product prices'
    
    def bulk_discount_apply(self, request, queryset):
        """Apply discount to selected products"""
        if 'apply' in request.POST:
            discount_percentage = request.POST.get('discount_percentage', 0)
            
            try:
                discount_percentage = float(discount_percentage)
                if not 0 <= discount_percentage <= 90:
                    raise ValueError("Discount must be between 0% and 90%")
                
                updated_count = 0
                
                for product in queryset:
                    # Set original price if not already set
                    if not product.original_price:
                        product.original_price = product.price
                    
                    # Calculate discounted price
                    discount_multiplier = 1 - (discount_percentage / 100)
                    product.price = (product.original_price * Decimal(str(discount_multiplier))).quantize(Decimal('0.01'))
                    
                    product.save()
                    updated_count += 1
                
                self.message_user(request, f'Applied {discount_percentage}% discount to {updated_count} products.')
                return
            except (ValueError, TypeError) as e:
                self.message_user(request, f'Error applying discount: {str(e)}', level=messages.ERROR)
        
        return render(request, 'admin/bulk_discount_apply.html', {
            'products': queryset,
            'title': 'Apply Bulk Discount'
        })
    bulk_discount_apply.short_description = 'Apply discount to selected products'
    
    def copy_prices_to_usd(self, request, queryset):
        """Convert INR prices to USD (for future multi-currency support)"""
        # Using approximate conversion rate - in production, use real-time rates
        inr_to_usd_rate = Decimal('0.012')  # 1 INR ≈ 0.012 USD
        
        converted_count = 0
        price_data = []
        
        for product in queryset:
            usd_price = (product.price * inr_to_usd_rate).quantize(Decimal('0.01'))
            usd_original = (product.original_price * inr_to_usd_rate).quantize(Decimal('0.01')) if product.original_price else None
            
            price_data.append({
                'product': product.name,
                'inr_price': product.price,
                'usd_price': usd_price,
                'inr_original': product.original_price,
                'usd_original': usd_original
            })
            converted_count += 1
        
        # For now, just show the conversion results
        self.message_user(request, f'Price conversion calculated for {converted_count} products. Check the response for details.')
        
        return render(request, 'admin/price_conversion_results.html', {
            'price_data': price_data,
            'title': 'INR to USD Price Conversion'
        })
    copy_prices_to_usd.short_description = 'Convert prices to USD (preview)'
    
    def smart_pricing_analysis(self, request, queryset):
        """Analyze pricing and provide recommendations"""
        analysis_data = []
        
        for product in queryset:
            # Get category average price for comparison
            category_avg = Product.objects.filter(
                category=product.category,
                available=True
            ).exclude(id=product.id).aggregate(avg_price=Avg('price'))['avg_price'] or 0
            
            # Price positioning analysis
            if category_avg > 0:
                price_vs_avg = ((product.price - category_avg) / category_avg) * 100
                if price_vs_avg > 20:
                    positioning = 'Premium'
                    recommendation = 'Consider if premium positioning is justified'
                elif price_vs_avg < -20:
                    positioning = 'Budget'
                    recommendation = 'Potential for price increase'
                else:
                    positioning = 'Competitive'
                    recommendation = 'Well-positioned in market'
            else:
                price_vs_avg = 0
                positioning = 'No comparison data'
                recommendation = 'Add more products in category for analysis'
            
            # Stock vs price analysis
            if product.stock > 50:
                stock_recommendation = 'High stock - consider promotion'
            elif product.stock < 5:
                stock_recommendation = 'Low stock - potential price increase'
            else:
                stock_recommendation = 'Stock level optimal'
            
            analysis_data.append({
                'product': product,
                'category_avg': category_avg,
                'price_vs_avg': price_vs_avg,
                'positioning': positioning,
                'recommendation': recommendation,
                'stock_recommendation': stock_recommendation,
                'profit_margin': product.get_discount_percentage()
            })
        
        return render(request, 'admin/smart_pricing_analysis.html', {
            'analysis_data': analysis_data,
            'title': 'Smart Pricing Analysis'
        })
    smart_pricing_analysis.short_description = 'Analyze pricing strategy'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = (
            'admin/js/enhanced_admin.js',
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__username', 'title']
    actions = ['approve_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} reviews approved.')
    approve_reviews.short_description = 'Approve selected reviews'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at', 'payment_method']
    search_fields = ['order_id', 'user__username', 'email']
    readonly_fields = ['order_id', 'created_at']
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def save_model(self, request, obj, form, change):
        if change:  # Only for updates
            # Get original status
            original_obj = Order.objects.get(pk=obj.pk)
            old_status = original_obj.status
            
            # Save the object first
            super().save_model(request, obj, form, change)
            
            # Send email if status changed
            if old_status != obj.status:
                try:
                    send_order_status_update_email(obj, old_status, obj.status)
                    self.message_user(request, f'Order status updated and email sent to customer.')
                except Exception as e:
                    self.message_user(request, f'Order updated but email failed: {str(e)}', level='WARNING')
        else:
            super().save_model(request, obj, form, change)
    
    def mark_as_processing(self, request, queryset):
        updated = 0
        for order in queryset:
            old_status = order.status
            order.status = 'processing'
            order.save()
            try:
                send_order_status_update_email(order, old_status, 'processing')
                updated += 1
            except Exception as e:
                self.message_user(request, f'Failed to send email for order {order.order_id}: {str(e)}', level='WARNING')
        self.message_user(request, f'{updated} orders marked as processing and emails sent.')
    mark_as_processing.short_description = 'Mark as processing (with email)'
    
    def mark_as_shipped(self, request, queryset):
        updated = 0
        for order in queryset:
            old_status = order.status
            order.status = 'shipped'
            order.save()
            try:
                send_order_status_update_email(order, old_status, 'shipped')
                updated += 1
            except Exception as e:
                self.message_user(request, f'Failed to send email for order {order.order_id}: {str(e)}', level='WARNING')
        self.message_user(request, f'{updated} orders marked as shipped and emails sent.')
    mark_as_shipped.short_description = 'Mark as shipped (with email)'
    
    def mark_as_delivered(self, request, queryset):
        updated = 0
        for order in queryset:
            old_status = order.status
            order.status = 'delivered'
            order.save()
            try:
                send_order_status_update_email(order, old_status, 'delivered')
                updated += 1
            except Exception as e:
                self.message_user(request, f'Failed to send email for order {order.order_id}: {str(e)}', level='WARNING')
        self.message_user(request, f'{updated} orders marked as delivered and emails sent.')
    mark_as_delivered.short_description = 'Mark as delivered (with email)'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'country']
    search_fields = ['user__username', 'user__email', 'phone']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def item_count(self, obj):
        return obj.get_item_count()
    item_count.short_description = 'Items'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['wishlist__user__username', 'product__name']
    readonly_fields = ['added_at']
    
    def user(self, obj):
        return obj.wishlist.user.username
    user.short_description = 'User'


@admin.register(ProductRecommendation)
class ProductRecommendationAdmin(admin.ModelAdmin):
    list_display = ['product', 'recommended_product', 'recommendation_type', 'score', 'created_at']
    list_filter = ['recommendation_type', 'created_at']
    search_fields = ['product__name', 'recommended_product__name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['regenerate_recommendations']
    
    def regenerate_recommendations(self, request, queryset):
        from .recommendations import recommendation_engine
        products = set(rec.product for rec in queryset)
        
        for product in products:
            # Generate new recommendations
            for rec_type in ['similar', 'frequently_bought']:
                recommendations = recommendation_engine.get_recommendations(
                    product=product,
                    recommendation_type=rec_type,
                    limit=10
                )
                
                # Clear existing
                ProductRecommendation.objects.filter(
                    product=product,
                    recommendation_type=rec_type
                ).delete()
                
                # Create new
                for i, rec_product in enumerate(recommendations):
                    score = max(0.1, 1.0 - (i * 0.05))
                    ProductRecommendation.objects.create(
                        product=product,
                        recommended_product=rec_product,
                        recommendation_type=rec_type,
                        score=score
                    )
        
        self.message_user(request, f'Regenerated recommendations for {len(products)} products.')
    regenerate_recommendations.short_description = 'Regenerate recommendations'


@admin.register(UserProductInteraction)
class UserProductInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'interaction_type', 'interaction_count', 'last_interaction']
    list_filter = ['interaction_type', 'last_interaction', 'created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at', 'last_interaction']


@admin.register(ProductComparison)
class ProductComparisonAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'product_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def product_count(self, obj):
        return obj.get_product_count()
    product_count.short_description = 'Products'


@admin.register(ComparisonItem)
class ComparisonItemAdmin(admin.ModelAdmin):
    list_display = ['comparison_name', 'user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['comparison__name', 'comparison__user__username', 'product__name']
    readonly_fields = ['added_at']
    
    def comparison_name(self, obj):
        return obj.comparison.name
    comparison_name.short_description = 'Comparison'
    
    def user(self, obj):
        return obj.comparison.user.username if obj.comparison.user else 'Anonymous'
    user.short_description = 'User'


@admin.register(InventorySettings)
class InventorySettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'low_stock_threshold', 'critical_stock_threshold', 'auto_create_alerts', 
                   'email_alerts', 'alert_frequency_hours', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return InventorySettings.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity_change', 'stock_before', 
                   'stock_after', 'reference_number', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference_number', 'notes']
    readonly_fields = ['created_at']
    actions = ['export_movements']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'movement_type', 'quantity_change')
        }),
        ('Stock Information', {
            'fields': ('stock_before', 'stock_after')
        }),
        ('References', {
            'fields': ('reference_number', 'notes', 'created_by')
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def export_movements(self, request, queryset):
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_movements.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Product', 'Movement Type', 'Quantity Change', 'Stock Before', 
                       'Stock After', 'Reference', 'Notes', 'Created By', 'Date'])
        
        for movement in queryset:
            writer.writerow([
                movement.product.name,
                movement.get_movement_type_display(),
                movement.quantity_change,
                movement.stock_before,
                movement.stock_after,
                movement.reference_number,
                movement.notes,
                movement.created_by.username if movement.created_by else 'System',
                movement.created_at.strftime('%Y-%m-%d %H:%M')
            ])
            
        return response
    export_movements.short_description = 'Export selected movements to CSV'


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'alert_level', 'current_stock', 'threshold', 
                   'is_resolved', 'created_at', 'resolved_at']
    list_filter = ['alert_level', 'is_resolved', 'created_at']
    search_fields = ['product__name']
    readonly_fields = ['created_at', 'resolved_at']
    actions = ['mark_as_resolved', 'send_low_stock_alert']
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} alerts marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected alerts as resolved'
    
    def send_low_stock_alert(self, request, queryset):
        from .emails import send_low_stock_alert_email
        sent_count = 0
        for alert in queryset:
            try:
                send_low_stock_alert_email(alert.product)
                sent_count += 1
            except Exception as e:
                self.message_user(request, f'Error sending alert for {alert.product.name}: {e}', 
                                 level=messages.ERROR)
        
        self.message_user(request, f'Sent {sent_count} low stock alert emails.')
    send_low_stock_alert.short_description = 'Send email alerts'


# ============================================================================
# CUSTOM ADMIN MODELS REGISTRATION
# ============================================================================

@admin.register(AdminRole)
class AdminRoleAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'display_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'theme_preference', 'two_factor_enabled', 'last_login_ip']
    list_filter = ['role', 'theme_preference', 'two_factor_enabled', 'email_notifications']
    search_fields = ['user__username', 'user__email', 'department', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'last_login_ip', 'failed_login_attempts']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'avatar', 'phone', 'department', 'bio')
        }),
        ('Preferences', {
            'fields': ('theme_preference', 'email_notifications', 'sms_notifications'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('two_factor_enabled', 'allowed_ip_addresses', 'last_login_ip', 
                      'failed_login_attempts', 'locked_until'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'get_action_type_display', 'description', 'object_type', 
                   'success', 'ip_address', 'timestamp']
    list_filter = ['action_type', 'success', 'timestamp']
    search_fields = ['admin_user__username', 'description', 'object_type']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Activity logs should not be manually added
    
    def has_change_permission(self, request, obj=None):
        return False  # Activity logs should not be changed


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'get_value_display', 'category', 'description', 'updated_at', 'updated_by']
    list_filter = ['category', 'is_secret']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_value_display(self, obj):
        if obj.is_secret:
            return '*** HIDDEN ***'
        return obj.value[:50] + ('...' if len(obj.value) > 50 else '')
    get_value_display.short_description = 'Value'
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AdminAnnouncement)
class AdminAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_announcement_type_display', 'is_active', 
                   'show_to_users', 'show_to_admins', 'created_by', 'created_at']
    list_filter = ['announcement_type', 'is_active', 'show_to_users', 'show_to_admins']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# CUSTOMIZE ADMIN SITE
# ============================================================================

admin.site.site_header = '🛒 CARTMAX - ADMIN DASHBOARD'
admin.site.site_title = 'CartMax Admin'
admin.site.index_title = '🌟 Welcome to CartMax Administration'

# Custom admin styling
admin.site.enable_nav_sidebar = False  # Disable sidebar for custom layout


# ============================================================================
# SEARCH & ANALYTICS ADMIN MODELS
# ============================================================================

@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.product_assignments.count()
    product_count.short_description = 'Products'


@admin.register(ProductTagAssignment)
class ProductTagAssignmentAdmin(admin.ModelAdmin):
    list_display = ['product', 'tag', 'created_at']
    list_filter = ['tag', 'created_at']
    search_fields = ['product__name', 'tag__name']
    autocomplete_fields = ['product', 'tag']


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'results_count', 'has_clicks', 'created_at']
    list_filter = ['results_count', 'created_at']
    search_fields = ['query', 'user__username']
    readonly_fields = ['query', 'user', 'session_key', 'ip_address', 'user_agent',
                      'category_filter', 'price_filter', 'brand_filter', 'sort_by',
                      'results_count', 'created_at']
    date_hierarchy = 'created_at'
    
    def has_clicks(self, obj):
        return obj.product_clicks.exists()
    has_clicks.boolean = True
    has_clicks.short_description = 'Has Clicks'
    
    def has_add_permission(self, request):
        return False  # Search queries are auto-generated
    
    def has_change_permission(self, request, obj=None):
        return False  # Read-only


@admin.register(SearchProductClick)
class SearchProductClickAdmin(admin.ModelAdmin):
    list_display = ['search_query_text', 'product', 'click_position', 'clicked_at']
    list_filter = ['click_position', 'clicked_at']
    search_fields = ['search_query__query', 'product__name']
    readonly_fields = ['search_query', 'product', 'click_position', 'clicked_at']
    date_hierarchy = 'clicked_at'
    
    def search_query_text(self, obj):
        return obj.search_query.query
    search_query_text.short_description = 'Search Query'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    list_display = ['query', 'search_count', 'last_searched']
    list_filter = ['last_searched']
    search_fields = ['query']
    readonly_fields = ['query', 'search_count', 'last_searched']
    ordering = ['-search_count', '-last_searched']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ============================================================================
# DISCOUNT COUPON ADMIN
# ============================================================================

@admin.register(DiscountCoupon)
class DiscountCouponAdmin(admin.ModelAdmin):
    """Admin interface for managing discount coupons"""
    list_display = ['coupon_code', 'discount_display', 'is_active_indicator', 'usage_display', 
                   'expiration_status', 'created_at']
    list_filter = ['discount_type', 'is_active', 'applicable_currencies', 'expiration_date', 'created_at']
    search_fields = ['coupon_code', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ['coupon_code', 'description', 'is_active']
        }),
        ('Discount Details', {
            'fields': ['discount_type', 'discount_value', 'applicable_currencies', 'amount_currency'],
            'description': 'Set the type and value of discount. Percentage values should be 0-100. Set the currency for min/max order amounts.'
        }),
        ('Usage Limits', {
            'fields': ['max_usage_limit', 'usage_count', 'expiration_date']
        }),
        ('Order Conditions', {
            'fields': ['minimum_order_amount', 'maximum_order_amount'],
            'description': 'Leave blank for no limit. Helpful for targeted promotions.'
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_coupons', 'deactivate_coupons', 'export_coupon_stats']
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new coupon"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.coupon_code = obj.coupon_code.upper().strip()  # Normalize coupon code
        super().save_model(request, obj, form, change)
    
    def discount_display(self, obj):
        """Display discount in readable format"""
        return format_html(
            '<strong>{}</strong> {}',
            obj.discount_value,
            '% off' if obj.discount_type == 'percentage' else 'off'
        )
    discount_display.short_description = 'Discount'
    
    def is_active_indicator(self, obj):
        """Visual indicator for coupon status"""
        color = '#28a745' if obj.is_active else '#6c757d'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    is_active_indicator.short_description = 'Status'
    
    def usage_display(self, obj):
        """Display usage count vs limit"""
        if obj.max_usage_limit:
            percent = (obj.usage_count / obj.max_usage_limit) * 100
            color = '#28a745' if percent < 50 else '#ffc107' if percent < 80 else '#dc3545'
            return format_html(
                '<span style="color: {};">{}/{}</span>',
                color,
                obj.usage_count,
                obj.max_usage_limit
            )
        return format_html('<span>{}/∞</span>', obj.usage_count)
    usage_display.short_description = 'Usage'
    
    def expiration_status(self, obj):
        """Display expiration status"""
        if not obj.expiration_date:
            return format_html('<span style="color: #999;">No expiration</span>')
        
        from django.utils import timezone
        if timezone.now() > obj.expiration_date:
            return format_html('<span style="color: #dc3545;">Expired</span>')
        
        return format_html('<span style="color: #28a745;">Active</span>')
    expiration_status.short_description = 'Expiration'
    
    def activate_coupons(self, request, queryset):
        """Bulk activate coupons"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} coupon(s) activated.')
    activate_coupons.short_description = 'Activate selected coupons'
    
    def deactivate_coupons(self, request, queryset):
        """Bulk deactivate coupons"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} coupon(s) deactivated.')
    deactivate_coupons.short_description = 'Deactivate selected coupons'
    
    def export_coupon_stats(self, request, queryset):
        """Export coupon statistics to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="coupon_stats.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Coupon Code', 'Type', 'Value', 'Status', 'Usage Count', 'Max Limit', 
                        'Min Order', 'Max Order', 'Expiration', 'Created'])
        
        for coupon in queryset:
            writer.writerow([
                coupon.coupon_code,
                coupon.get_discount_type_display(),
                coupon.discount_value,
                'Active' if coupon.is_active else 'Inactive',
                coupon.usage_count,
                coupon.max_usage_limit or 'Unlimited',
                coupon.minimum_order_amount or 'None',
                coupon.maximum_order_amount or 'None',
                coupon.expiration_date.strftime('%Y-%m-%d') if coupon.expiration_date else 'None',
                coupon.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    export_coupon_stats.short_description = 'Export statistics to CSV'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    """Admin interface for tracking coupon usage per user"""
    list_display = ['coupon_code', 'username', 'usage_count', 'last_used_at']
    list_filter = ['coupon', 'last_used_at']
    search_fields = ['coupon__coupon_code', 'user__username', 'user__email']
    readonly_fields = ['last_used_at', 'coupon', 'user']
    
    fieldsets = (
        ('Coupon Usage', {
            'fields': ['coupon', 'user', 'usage_count']
        }),
        ('Timestamps', {
            'fields': ['last_used_at'],
            'classes': ('collapse',)
        }),
    )
    
    def coupon_code(self, obj):
        """Display coupon code"""
        return obj.coupon.coupon_code
    coupon_code.short_description = 'Coupon Code'
    coupon_code.admin_order_field = 'coupon__coupon_code'
    
    def username(self, obj):
        """Display username"""
        return obj.user.username
    username.short_description = 'User'
    username.admin_order_field = 'user__username'
    
    def has_add_permission(self, request):
        """Prevent manual creation of usage records"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of usage records (maintain audit trail)"""
        return False
