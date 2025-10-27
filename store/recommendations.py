from django.db.models import Count, Q, Avg, F
from django.contrib.auth.models import User
from .models import Product, ProductRecommendation, UserProductInteraction, Order, OrderItem, Review
from collections import defaultdict
import random
from datetime import datetime, timedelta
from decimal import Decimal

class RecommendationEngine:
    """
    Advanced product recommendation engine with multiple algorithms
    """
    
    def __init__(self):
        self.algorithms = {
            'similar': self.get_similar_products,
            'frequently_bought': self.get_frequently_bought_together,
            'popular': self.get_popular_products,
            'user_based': self.get_user_based_recommendations,
            'trending': self.get_trending_products,
        }
    
    def get_recommendations(self, product=None, user=None, recommendation_type='similar', limit=8):
        """
        Get product recommendations based on type
        """
        if recommendation_type in self.algorithms:
            return self.algorithms[recommendation_type](product, user, limit)
        return []
    
    def get_similar_products(self, product, user=None, limit=8):
        """
        Find similar products based on category, brand, price range
        """
        if not product:
            return []
        
        similar_products = Product.objects.filter(
            available=True
        ).exclude(id=product.id)
        
        # Same category gets highest priority
        category_products = similar_products.filter(category=product.category)
        
        # Similar price range (±30%)
        price_min = product.price * Decimal('0.7')
        price_max = product.price * Decimal('1.3')
        price_range_products = similar_products.filter(
            price__gte=price_min,
            price__lte=price_max
        )
        
        # Same brand
        brand_products = similar_products.filter(brand=product.brand) if product.brand else Product.objects.none()
        
        # Combine and prioritize
        recommendations = []
        
        # Add category matches first
        for p in category_products[:limit//2]:
            if p not in recommendations:
                recommendations.append(p)
        
        # Add brand matches
        for p in brand_products[:limit//4]:
            if p not in recommendations and len(recommendations) < limit:
                recommendations.append(p)
        
        # Add price range matches
        for p in price_range_products:
            if p not in recommendations and len(recommendations) < limit:
                recommendations.append(p)
        
        # Fill remaining with popular products from same category
        if len(recommendations) < limit:
            popular_in_category = category_products.annotate(
                order_count=Count('orderitem')
            ).order_by('-order_count', '-created_at')
            
            for p in popular_in_category:
                if p not in recommendations and len(recommendations) < limit:
                    recommendations.append(p)
        
        return recommendations[:limit]
    
    def get_frequently_bought_together(self, product, user=None, limit=8):
        """
        Find products frequently bought together with the given product
        """
        if not product:
            return []
        
        # Get orders that contain this product
        orders_with_product = Order.objects.filter(
            items__product=product,
            status__in=['processing', 'shipped', 'delivered']
        ).prefetch_related('items__product')
        
        # Count co-occurrences
        product_counts = defaultdict(int)
        
        for order in orders_with_product:
            for item in order.items.all():
                if item.product != product and item.product.available:
                    product_counts[item.product] += 1
        
        # Sort by frequency and return top products
        frequently_bought = sorted(
            product_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [product for product, count in frequently_bought[:limit]]
    
    def get_popular_products(self, product=None, user=None, limit=8):
        """
        Get currently popular products based on recent orders and views
        """
        # Get products with most orders in the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        popular_products = Product.objects.filter(
            available=True
        ).annotate(
            recent_orders=Count(
                'orderitem__order',
                filter=Q(orderitem__order__created_at__gte=thirty_days_ago)
            ),
            total_orders=Count('orderitem'),
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).order_by(
            '-recent_orders',
            '-total_orders',
            '-avg_rating'
        )
        
        if product:
            popular_products = popular_products.exclude(id=product.id)
        
        return list(popular_products[:limit])
    
    def get_user_based_recommendations(self, product=None, user=None, limit=8):
        """
        Get personalized recommendations based on user's purchase history and preferences
        """
        if not user or not user.is_authenticated:
            return self.get_popular_products(product, user, limit)
        
        # Get user's purchase history
        purchased_products = Product.objects.filter(
            orderitem__order__user=user,
            orderitem__order__status__in=['processing', 'shipped', 'delivered']
        ).distinct()
        
        # Get user's wishlist items
        wishlisted_products = Product.objects.filter(
            wishlistitem__wishlist__user=user
        ).distinct()
        
        # Get user's reviewed products
        reviewed_products = Product.objects.filter(
            reviews__user=user
        ).distinct()
        
        # Find categories user likes
        preferred_categories = []
        for p in purchased_products:
            preferred_categories.append(p.category)
        
        # Get similar products from preferred categories
        recommendations = []
        
        if preferred_categories:
            similar_products = Product.objects.filter(
                category__in=preferred_categories,
                available=True
            ).exclude(
                id__in=[p.id for p in purchased_products]
            ).exclude(
                id__in=[p.id for p in wishlisted_products]
            ).annotate(
                order_count=Count('orderitem'),
                avg_rating=Avg('reviews__rating')
            ).order_by('-order_count', '-avg_rating')
            
            recommendations.extend(list(similar_products[:limit//2]))
        
        # Fill remaining with collaborative filtering
        if len(recommendations) < limit:
            # Find users with similar purchase patterns
            similar_users = User.objects.filter(
                orders__items__product__in=purchased_products
            ).exclude(id=user.id).annotate(
                common_products=Count('orders__items__product', filter=Q(orders__items__product__in=purchased_products))
            ).filter(common_products__gte=2).order_by('-common_products')[:10]
            
            # Get products bought by similar users
            collaborative_products = Product.objects.filter(
                orderitem__order__user__in=similar_users,
                available=True
            ).exclude(
                id__in=[p.id for p in purchased_products]
            ).exclude(
                id__in=[r.id for r in recommendations]
            ).annotate(
                similarity_score=Count('orderitem')
            ).order_by('-similarity_score')
            
            for p in collaborative_products:
                if len(recommendations) < limit:
                    recommendations.append(p)
        
        # Fill remaining with popular products
        if len(recommendations) < limit:
            popular = self.get_popular_products(None, user, limit - len(recommendations))
            for p in popular:
                if p not in recommendations:
                    recommendations.append(p)
        
        return recommendations[:limit]
    
    def get_trending_products(self, product=None, user=None, limit=8):
        """
        Get trending products based on recent activity
        """
        # Products with high recent activity (orders, reviews, views)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        trending = Product.objects.filter(
            available=True
        ).annotate(
            recent_orders=Count(
                'orderitem__order',
                filter=Q(orderitem__order__created_at__gte=seven_days_ago)
            ),
            recent_reviews=Count(
                'reviews',
                filter=Q(reviews__created_at__gte=seven_days_ago)
            ),
            recent_interactions=Count(
                'user_interactions',
                filter=Q(user_interactions__last_interaction__gte=seven_days_ago)
            )
        ).filter(
            Q(recent_orders__gt=0) | Q(recent_reviews__gt=0) | Q(recent_interactions__gt=0)
        ).order_by(
            '-recent_orders',
            '-recent_reviews',
            '-recent_interactions'
        )
        
        if product:
            trending = trending.exclude(id=product.id)
        
        return list(trending[:limit])
    
    def track_interaction(self, user, product, interaction_type):
        """
        Track user interaction with a product
        """
        if not user or not user.is_authenticated:
            return
        
        interaction, created = UserProductInteraction.objects.get_or_create(
            user=user,
            product=product,
            interaction_type=interaction_type,
            defaults={'interaction_count': 1}
        )
        
        if not created:
            interaction.interaction_count = F('interaction_count') + 1
            interaction.save(update_fields=['interaction_count', 'last_interaction'])
    
    def generate_recommendations_batch(self, limit_per_type=100):
        """
        Generate and store recommendations for all products (run as management command)
        """
        products = Product.objects.filter(available=True)
        
        for product in products:
            # Generate different types of recommendations
            for rec_type in ['similar', 'frequently_bought']:
                recommendations = self.get_recommendations(
                    product=product, 
                    recommendation_type=rec_type, 
                    limit=20
                )
                
                # Clear existing recommendations of this type
                ProductRecommendation.objects.filter(
                    product=product,
                    recommendation_type=rec_type
                ).delete()
                
                # Store new recommendations
                for i, rec_product in enumerate(recommendations):
                    score = max(Decimal('0.1'), Decimal('1.0') - (i * Decimal('0.05')))  # Decreasing score
                    
                    ProductRecommendation.objects.create(
                        product=product,
                        recommended_product=rec_product,
                        recommendation_type=rec_type,
                        score=score
                    )
    
    def get_stored_recommendations(self, product, recommendation_type='similar', limit=8):
        """
        Get pre-computed recommendations from database
        """
        stored_recs = ProductRecommendation.objects.filter(
            product=product,
            recommendation_type=recommendation_type,
            recommended_product__available=True
        ).select_related('recommended_product')[:limit]
        
        return [rec.recommended_product for rec in stored_recs]


# Global instance
recommendation_engine = RecommendationEngine()