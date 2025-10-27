"""
Coupon Analytics & Reporting Module
Provides statistics, performance metrics, and analysis for discount coupons
"""

from django.db.models import Count, Sum, Avg, Q, F, DecimalField, Value
from django.db.models.functions import TruncDate, Cast
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from .models import DiscountCoupon, CouponUsage, Order, OrderItem
import json


class CouponAnalytics:
    """Comprehensive analytics for discount coupons"""
    
    @staticmethod
    def get_overall_statistics(start_date=None, end_date=None):
        """
        Get overall coupon system statistics
        
        Returns:
            dict: Overall stats including total coupons, usage, revenue impact
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        # Filter orders by date range
        orders_with_coupons = Order.objects.filter(
            applied_coupon__isnull=False,
            created_at__range=[start_date, end_date]
        )
        
        total_coupons = DiscountCoupon.objects.count()
        active_coupons = DiscountCoupon.objects.filter(is_active=True).count()
        expired_coupons = DiscountCoupon.objects.filter(
            expiration_date__lt=timezone.now()
        ).count()
        
        total_discount_given = orders_with_coupons.aggregate(
            total=Sum('discount_amount')
        )['total'] or Decimal('0')
        
        total_orders = orders_with_coupons.count()
        avg_discount_per_order = total_discount_given / total_orders if total_orders > 0 else Decimal('0')
        
        total_revenue_without_discount = orders_with_coupons.aggregate(
            total=Sum('original_subtotal')
        )['total'] or Decimal('0')
        
        revenue_with_discount = orders_with_coupons.aggregate(
            total=Sum(F('original_subtotal') - F('discount_amount'), output_field=DecimalField())
        )['total'] or Decimal('0')
        
        discount_percentage = (total_discount_given / total_revenue_without_discount * 100) if total_revenue_without_discount > 0 else Decimal('0')
        
        return {
            'total_coupons': total_coupons,
            'active_coupons': active_coupons,
            'expired_coupons': expired_coupons,
            'total_orders_with_coupon': total_orders,
            'total_discount_given': float(total_discount_given),
            'average_discount_per_order': float(avg_discount_per_order),
            'total_revenue_without_discount': float(total_revenue_without_discount),
            'total_revenue_with_discount': float(revenue_with_discount),
            'discount_percentage': float(discount_percentage),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            }
        }
    
    @staticmethod
    def get_coupon_performance(coupon_id=None, start_date=None, end_date=None):
        """
        Get detailed performance metrics for a specific coupon
        
        Args:
            coupon_id: ID of coupon to analyze (None = all coupons)
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            dict or list: Performance metrics for coupon(s)
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        def calculate_performance(coupon):
            orders = Order.objects.filter(
                applied_coupon=coupon,
                created_at__range=[start_date, end_date]
            )
            
            usage_count = orders.count()
            total_discount = orders.aggregate(Sum('discount_amount'))['discount_amount__sum'] or Decimal('0')
            original_revenue = orders.aggregate(Sum('original_subtotal'))['original_subtotal__sum'] or Decimal('0')
            
            conversion_value = original_revenue - total_discount if original_revenue > 0 else Decimal('0')
            roi = (total_discount / total_discount) * 100 if total_discount > 0 else Decimal('0')  # Simplified
            
            return {
                'coupon_id': coupon.id,
                'code': coupon.coupon_code,
                'discount_type': coupon.get_discount_type_display(),
                'discount_value': float(coupon.discount_value),
                'is_active': coupon.is_active,
                'usage_count': usage_count,
                'max_limit': coupon.max_usage_limit,
                'total_discount_given': float(total_discount),
                'original_revenue': float(original_revenue),
                'final_revenue': float(conversion_value),
                'revenue_impact': float(original_revenue - conversion_value),
                'average_discount': float(total_discount / usage_count) if usage_count > 0 else 0,
                'roi_percentage': float(roi),
                'created_at': coupon.created_at.isoformat(),
                'expiration_date': coupon.expiration_date.isoformat() if coupon.expiration_date else None,
            }
        
        if coupon_id:
            coupon = DiscountCoupon.objects.get(id=coupon_id)
            return calculate_performance(coupon)
        else:
            coupons = DiscountCoupon.objects.all()
            return [calculate_performance(c) for c in coupons]
    
    @staticmethod
    def get_top_performing_coupons(limit=10, start_date=None, end_date=None):
        """
        Get top performing coupons by revenue impact
        
        Returns:
            list: Top coupons ranked by effectiveness
        """
        performances = CouponAnalytics.get_coupon_performance(
            coupon_id=None, 
            start_date=start_date, 
            end_date=end_date
        )
        
        # Sort by total discount given (most popular)
        sorted_by_usage = sorted(
            performances, 
            key=lambda x: x['usage_count'], 
            reverse=True
        )[:limit]
        
        return sorted_by_usage
    
    @staticmethod
    def get_user_coupon_usage(user_id, start_date=None, end_date=None):
        """
        Get coupon usage statistics for a specific user
        
        Args:
            user_id: ID of user to analyze
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            dict: User's coupon usage statistics
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=90)
        if not end_date:
            end_date = timezone.now()
        
        user_orders = Order.objects.filter(
            user_id=user_id,
            applied_coupon__isnull=False,
            created_at__range=[start_date, end_date]
        )
        
        total_savings = user_orders.aggregate(Sum('discount_amount'))['discount_amount__sum'] or Decimal('0')
        order_count = user_orders.count()
        coupons_used = user_orders.values('applied_coupon__coupon_code').distinct().count()
        
        usage_details = CouponUsage.objects.filter(user_id=user_id).values(
            'coupon__coupon_code',
            'usage_count',
            'last_used_at'
        )
        
        return {
            'user_id': user_id,
            'total_orders_with_coupon': order_count,
            'total_savings': float(total_savings),
            'average_savings_per_order': float(total_savings / order_count) if order_count > 0 else 0,
            'unique_coupons_used': coupons_used,
            'coupon_details': list(usage_details),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            }
        }
    
    @staticmethod
    def get_usage_trends(days=30, group_by='day'):
        """
        Get coupon usage trends over time
        
        Args:
            days: Number of days to look back
            group_by: 'day', 'week', or 'month'
            
        Returns:
            list: Daily/weekly/monthly usage statistics
        """
        start_date = timezone.now() - timedelta(days=days)
        
        orders = Order.objects.filter(
            applied_coupon__isnull=False,
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            order_count=Count('id'),
            total_discount=Sum('discount_amount'),
            total_revenue=Sum(F('original_subtotal') - F('discount_amount'), output_field=DecimalField())
        ).order_by('date')
        
        return [
            {
                'date': order['date'].isoformat(),
                'order_count': order['order_count'],
                'total_discount': float(order['total_discount'] or 0),
                'total_revenue': float(order['total_revenue'] or 0),
                'average_discount': float((order['total_discount'] or 0) / order['order_count']) if order['order_count'] > 0 else 0,
            }
            for order in orders
        ]
    
    @staticmethod
    def get_coupon_comparison(coupon_ids, start_date=None, end_date=None):
        """
        Compare performance of multiple coupons
        
        Args:
            coupon_ids: List of coupon IDs to compare
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            dict: Comparison data for all specified coupons
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        comparison = {}
        for coupon_id in coupon_ids:
            coupon = DiscountCoupon.objects.get(id=coupon_id)
            performance = CouponAnalytics.get_coupon_performance(coupon_id, start_date, end_date)
            comparison[coupon.coupon_code] = performance
        
        return comparison
    
    @staticmethod
    def get_roi_metrics(start_date=None, end_date=None):
        """
        Calculate ROI metrics for coupon campaigns
        
        Returns:
            dict: ROI and effectiveness metrics
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        orders_with_coupons = Order.objects.filter(
            applied_coupon__isnull=False,
            created_at__range=[start_date, end_date]
        )
        
        total_discount = orders_with_coupons.aggregate(Sum('discount_amount'))['discount_amount__sum'] or Decimal('0')
        orders_count = orders_with_coupons.count()
        new_customers_with_coupon = orders_with_coupons.values('user_id').distinct().count()
        
        # Customer acquisition benefit (if they use coupon first purchase)
        repeat_orders = Order.objects.filter(
            user__in=orders_with_coupons.values_list('user_id', flat=True)
        ).exclude(applied_coupon__isnull=False).count()
        
        return {
            'total_discount_cost': float(total_discount),
            'orders_generated': orders_count,
            'unique_users_acquired': new_customers_with_coupon,
            'discount_per_order': float(total_discount / orders_count) if orders_count > 0 else 0,
            'cost_per_acquisition': float(total_discount / new_customers_with_coupon) if new_customers_with_coupon > 0 else 0,
            'customer_retention_boost': repeat_orders,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            }
        }
    
    @staticmethod
    def export_coupon_report(format='json', start_date=None, end_date=None):
        """
        Export comprehensive coupon report
        
        Args:
            format: 'json' or 'csv'
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            str: Report data in requested format
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        report_data = {
            'generated_at': timezone.now().isoformat(),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'overall_statistics': CouponAnalytics.get_overall_statistics(start_date, end_date),
            'coupon_performance': CouponAnalytics.get_coupon_performance(None, start_date, end_date),
            'usage_trends': CouponAnalytics.get_usage_trends(30, 'day'),
            'roi_metrics': CouponAnalytics.get_roi_metrics(start_date, end_date),
        }
        
        if format == 'json':
            return json.dumps(report_data, indent=2, default=str)
        elif format == 'csv':
            # CSV export can be implemented separately
            return CouponAnalytics._generate_csv_report(report_data)
        
        return report_data
    
    @staticmethod
    def _generate_csv_report(data):
        """
        Generate CSV format report
        
        Args:
            data: Report data dictionary
            
        Returns:
            str: CSV formatted report
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Overall statistics
        writer.writerow(['Overall Statistics'])
        stats = data['overall_statistics']
        for key, value in stats.items():
            if key != 'date_range':
                writer.writerow([key, value])
        
        writer.writerow([])
        
        # Coupon performance
        writer.writerow(['Coupon Performance'])
        writer.writerow(['Code', 'Type', 'Usage Count', 'Total Discount', 'Original Revenue', 'Final Revenue', 'ROI %'])
        for coupon in data['coupon_performance']:
            writer.writerow([
                coupon['code'],
                coupon['discount_type'],
                coupon['usage_count'],
                coupon['total_discount_given'],
                coupon['original_revenue'],
                coupon['final_revenue'],
                coupon['roi_percentage'],
            ])
        
        return output.getvalue()


# Convenience functions
def get_analytics(metric='overview', **kwargs):
    """
    Convenience function to get specific analytics
    
    Args:
        metric: 'overview', 'performance', 'trends', 'roi', 'top', 'user', 'comparison'
        **kwargs: Additional parameters for specific metrics
        
    Returns:
        Analytics data
    """
    if metric == 'overview':
        return CouponAnalytics.get_overall_statistics(
            kwargs.get('start_date'),
            kwargs.get('end_date')
        )
    elif metric == 'performance':
        return CouponAnalytics.get_coupon_performance(
            kwargs.get('coupon_id'),
            kwargs.get('start_date'),
            kwargs.get('end_date')
        )
    elif metric == 'trends':
        return CouponAnalytics.get_usage_trends(
            kwargs.get('days', 30),
            kwargs.get('group_by', 'day')
        )
    elif metric == 'roi':
        return CouponAnalytics.get_roi_metrics(
            kwargs.get('start_date'),
            kwargs.get('end_date')
        )
    elif metric == 'top':
        return CouponAnalytics.get_top_performing_coupons(
            kwargs.get('limit', 10),
            kwargs.get('start_date'),
            kwargs.get('end_date')
        )
    elif metric == 'user':
        return CouponAnalytics.get_user_coupon_usage(
            kwargs.get('user_id'),
            kwargs.get('start_date'),
            kwargs.get('end_date')
        )
    elif metric == 'comparison':
        return CouponAnalytics.get_coupon_comparison(
            kwargs.get('coupon_ids', []),
            kwargs.get('start_date'),
            kwargs.get('end_date')
        )
    
    return {}
