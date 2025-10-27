from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_order_confirmation_email(order):
    """
    Send order confirmation email to the customer
    """
    try:
        subject = f'Order Confirmation #{order.order_number} - CartMax'
        
        # Render HTML template
        html_content = render_to_string('emails/order_confirmation.html', {'order': order})
        
        # Render text template
        text_content = render_to_string('emails/order_confirmation.txt', {'order': order})
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Order confirmation email sent successfully for order #{order.order_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.order_number}: {str(e)}")
        return False

def send_order_status_update_email(order, old_status, new_status):
    """
    Send email when order status changes
    """
    try:
        subject = f'Order Status Update #{order.order_number} - CartMax'
        
        context = {
            'order': order,
            'old_status': old_status,
            'new_status': new_status,
        }
        
        # Simple text email for status updates
        message = f"""
Hi {order.user.first_name if order.user.first_name else order.user.username},

Your order #{order.order_number} status has been updated.

Previous Status: {old_status}
New Status: {new_status}

You can track your order at: http://127.0.0.1:8000/order/{order.id}/

Thank you for shopping with CartMax!

Best regards,
The CartMax Team
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=message.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        
        email.send()
        
        logger.info(f"Order status update email sent for order #{order.order_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order status update email for order #{order.order_number}: {str(e)}")
        return False

def send_low_stock_alert_email(product):
    """
    Send low stock alert to admin
    """
    try:
        subject = f'Low Stock Alert: {product.name} - CartMax'
        
        message = f"""
Low Stock Alert!

Product: {product.name}
Current Stock: {getattr(product, 'stock_quantity', 'N/A')}
SKU: {getattr(product, 'sku', 'N/A')}

Please restock this item soon.

CartMax Admin System
        """
        
        admin_emails = [admin[1] for admin in settings.ADMINS]
        
        if admin_emails:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=admin_emails,
            )
            
            email.send()
            
            logger.info(f"Low stock alert email sent for product: {product.name}")
            return True
        
    except Exception as e:
        logger.error(f"Failed to send low stock alert email for product {product.name}: {str(e)}")
        return False