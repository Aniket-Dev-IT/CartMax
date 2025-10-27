from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Product, InventoryMovement, LowStockAlert, InventorySettings
from .emails import send_low_stock_alert_email
from django.contrib.auth.models import User

class InventoryManager:
    """
    Centralized inventory management system
    """
    
    def __init__(self):
        try:
            self.settings = self.get_settings()
        except Exception:
            # During migrations, tables might not exist yet
            self.settings = None
    
    def get_settings(self):
        """Get or create inventory settings"""
        settings, created = InventorySettings.objects.get_or_create(
            id=1,
            defaults={
                'low_stock_threshold': 10,
                'critical_stock_threshold': 5,
                'auto_create_alerts': True,
                'email_alerts': True,
                'alert_frequency_hours': 24,
            }
        )
        return settings
    
    @transaction.atomic
    def update_stock(self, product, quantity_change, movement_type, reference_number='', notes='', created_by=None):
        """
        Update product stock and create inventory movement record
        """
        if isinstance(product, int):
            product = Product.objects.get(id=product)
        
        # Record current stock
        stock_before = product.stock
        
        # Calculate new stock
        new_stock = max(0, stock_before + quantity_change)
        
        # Update product stock
        product.stock = new_stock
        product.save()
        
        # Create inventory movement record
        movement = InventoryMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity_change=quantity_change,
            stock_before=stock_before,
            stock_after=new_stock,
            reference_number=reference_number,
            notes=notes,
            created_by=created_by
        )
        
        # Check for stock alerts
        if self.settings and self.settings.auto_create_alerts:
            self.check_stock_alerts(product)
        
        return movement
    
    def check_stock_alerts(self, product):
        """
        Check if product needs stock alerts and create them
        """
        if not self.settings:
            return None
            
        current_stock = product.stock
        
        # Determine alert level
        alert_level = None
        if current_stock == 0:
            alert_level = 'out_of_stock'
            threshold = 0
        elif current_stock <= self.settings.critical_stock_threshold:
            alert_level = 'critical'
            threshold = self.settings.critical_stock_threshold
        elif current_stock <= self.settings.low_stock_threshold:
            alert_level = 'low'
            threshold = self.settings.low_stock_threshold
        
        if alert_level:
            # Check if alert already exists and is unresolved
            existing_alert = LowStockAlert.objects.filter(
                product=product,
                alert_level=alert_level,
                is_resolved=False
            ).first()
            
            if not existing_alert:
                # Create new alert
                alert = LowStockAlert.objects.create(
                    product=product,
                    alert_level=alert_level,
                    threshold=threshold,
                    current_stock=current_stock
                )
                
                # Send email alert if enabled
                if self.settings and self.settings.email_alerts:
                    try:
                        send_low_stock_alert_email(product)
                    except Exception as e:
                        print(f"Failed to send low stock alert email: {e}")
                
                return alert
        else:
            # Resolve existing alerts if stock is sufficient
            LowStockAlert.objects.filter(
                product=product,
                is_resolved=False
            ).update(
                is_resolved=True,
                resolved_at=timezone.now()
            )
        
        return None
    
    def bulk_stock_update(self, stock_updates, movement_type='adjustment', notes='Bulk update', created_by=None):
        """
        Update stock for multiple products
        stock_updates: list of dicts with 'product_id', 'quantity_change'
        """
        movements = []
        
        with transaction.atomic():
            for update in stock_updates:
                try:
                    product = Product.objects.get(id=update['product_id'])
                    quantity_change = update['quantity_change']
                    
                    movement = self.update_stock(
                        product=product,
                        quantity_change=quantity_change,
                        movement_type=movement_type,
                        notes=notes,
                        created_by=created_by
                    )
                    movements.append(movement)
                    
                except Product.DoesNotExist:
                    continue
        
        return movements
    
    def get_low_stock_products(self, alert_level='low'):
        """
        Get products with active low stock alerts
        """
        return Product.objects.filter(
            stock_alerts__alert_level=alert_level,
            stock_alerts__is_resolved=False
        ).distinct()
    
    def get_stock_report(self, category=None, days=30):
        """
        Generate stock movement report
        """
        from datetime import timedelta
        from django.db.models import Sum, Count
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset
        movements = InventoryMovement.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if category:
            movements = movements.filter(product__category=category)
        
        # Aggregate data
        report = {
            'total_movements': movements.count(),
            'stock_in': movements.filter(quantity_change__gt=0).aggregate(
                total=Sum('quantity_change')
            )['total'] or 0,
            'stock_out': movements.filter(quantity_change__lt=0).aggregate(
                total=Sum('quantity_change')
            )['total'] or 0,
            'by_type': movements.values('movement_type').annotate(
                count=Count('id'),
                total_change=Sum('quantity_change')
            ).order_by('-count'),
            'top_products': movements.values(
                'product__name', 'product__id'
            ).annotate(
                movement_count=Count('id'),
                total_change=Sum('quantity_change')
            ).order_by('-movement_count')[:10]
        }
        
        return report
    
    def restock_suggestion(self, product, days_of_supply=30):
        """
        Suggest restock quantity based on sales velocity
        """
        from datetime import timedelta
        
        # Calculate average daily sales
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        sales_movements = InventoryMovement.objects.filter(
            product=product,
            movement_type='sale',
            created_at__gte=start_date
        ).aggregate(
            total_sold=Sum('quantity_change')
        )['total_sold'] or 0
        
        # Make positive (sales are recorded as negative)
        total_sold = abs(sales_movements)
        daily_velocity = total_sold / 30 if total_sold > 0 else 1
        
        # Calculate suggested restock quantity
        target_stock = daily_velocity * days_of_supply
        current_stock = product.stock
        suggested_restock = max(0, target_stock - current_stock)
        
        return {
            'current_stock': current_stock,
            'daily_velocity': round(daily_velocity, 2),
            'days_of_supply_current': round(current_stock / daily_velocity, 1) if daily_velocity > 0 else float('inf'),
            'suggested_restock': round(suggested_restock),
            'target_stock': round(target_stock)
        }
    
    def auto_restock_check(self):
        """
        Check all products that might need restocking
        """
        suggestions = []
        
        # Get products with critical or low stock
        low_stock_products = self.get_low_stock_products('low')
        critical_stock_products = self.get_low_stock_products('critical')
        
        all_products = set(list(low_stock_products) + list(critical_stock_products))
        
        for product in all_products:
            suggestion = self.restock_suggestion(product)
            suggestion['product'] = product
            suggestion['priority'] = 'critical' if product in critical_stock_products else 'low'
            suggestions.append(suggestion)
        
        # Sort by priority and days of supply
        suggestions.sort(key=lambda x: (
            0 if x['priority'] == 'critical' else 1,
            x['days_of_supply_current']
        ))
        
        return suggestions


# Global instance
inventory_manager = InventoryManager()