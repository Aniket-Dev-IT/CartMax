"""
Advanced Search Management System for CartMax
Handles product search, filtering, and relevance scoring
"""

from django.db.models import Q, F, Count, Avg, Case, When, IntegerField, Value, Min, Max
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import re
import operator
from functools import reduce
from .models import Product, Category, SearchQuery as SearchQueryModel, PopularSearch, ProductTag


class SearchManager:
    """Advanced search manager for products with relevance scoring and filtering"""
    
    def __init__(self):
        self.default_per_page = 12
        self.max_per_page = 48
    
    def search_products(self, query='', filters=None, sort_by='relevance', page=1, per_page=12):
        """
        Main search method with advanced filtering and relevance scoring
        
        Args:
            query: Search query string
            filters: Dictionary of filters to apply
            sort_by: Sorting method ('relevance', 'price-low', 'price-high', 'rating', 'newest')
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            Dictionary with search results, pagination info, and filter options
        """
        filters = filters or {}
        per_page = min(per_page, self.max_per_page)
        
        # Start with all available products
        queryset = Product.objects.filter(available=True).select_related('category')
        
        # Apply text search with relevance scoring
        if query:
            queryset = self._apply_text_search(queryset, query)
        
        # Apply filters
        queryset = self._apply_filters(queryset, filters)
        
        # Get filter options before pagination
        filter_options = self._get_filter_options(queryset, query, filters)
        
        # Apply sorting
        queryset = self._apply_sorting(queryset, sort_by, query)
        
        # Pagination
        paginator = Paginator(queryset, per_page)
        products = paginator.get_page(page)
        
        return {
            'products': products,
            'filter_options': filter_options,
            'query': query,
            'sort_by': sort_by,
            'total_results': paginator.count,
            'page_info': {
                'current': page,
                'total_pages': paginator.num_pages,
                'has_previous': products.has_previous(),
                'has_next': products.has_next(),
                'previous_page': products.previous_page_number() if products.has_previous() else None,
                'next_page': products.next_page_number() if products.has_next() else None,
            }
        }
    
    def _apply_text_search(self, queryset, query):
        """Apply text search with relevance scoring"""
        if not query:
            return queryset
        
        # Clean and prepare query
        query = query.strip()
        query_terms = self._extract_search_terms(query)
        
        if not query_terms:
            return queryset
        
        # Build search conditions with different weights for different fields
        search_conditions = Q()
        
        for term in query_terms:
            term_condition = (
                # High priority: exact matches in name and brand
                Q(name__iexact=term) |
                Q(brand__iexact=term) |
                # Medium-high priority: starts with matches
                Q(name__istartswith=term) |
                Q(brand__istartswith=term) |
                # Medium priority: contains matches
                Q(name__icontains=term) |
                Q(brand__icontains=term) |
                Q(description__icontains=term) |
                Q(short_description__icontains=term) |
                Q(search_keywords__icontains=term) |
                Q(category__name__icontains=term) |
                # Lower priority: specifications and tags
                Q(specifications__value__icontains=term) |
                Q(tag_assignments__tag__name__icontains=term)
            )
            search_conditions |= term_condition
        
        # Apply search conditions
        queryset = queryset.filter(search_conditions).distinct()
        
        # Add relevance scoring
        queryset = self._add_relevance_score(queryset, query_terms)
        
        return queryset
    
    def _add_relevance_score(self, queryset, query_terms):
        """Add relevance scoring to search results"""
        # First calculate base relevance score
        base_relevance = Case(
            # Highest priority: exact name match
            When(name__iexact=' '.join(query_terms), then=Value(100)),
            # High priority: name starts with query
            When(name__istartswith=' '.join(query_terms), then=Value(90)),
            # Name contains all terms
            When(reduce(operator.and_, [Q(name__icontains=term) for term in query_terms]), then=Value(80)),
            # Brand exact match
            When(brand__iexact=' '.join(query_terms), then=Value(75)),
            # Brand contains terms
            When(reduce(operator.or_, [Q(brand__icontains=term) for term in query_terms]), then=Value(70)),
            default=Value(50),
            output_field=IntegerField()
        )
        
        # Then add featured product bonus
        final_relevance = Case(
            When(featured=True, then=base_relevance + Value(10)),
            default=base_relevance,
            output_field=IntegerField()
        )
        
        return queryset.annotate(
            relevance_score=final_relevance
        )
    
    def _extract_search_terms(self, query):
        """Extract meaningful search terms from query"""
        # Remove special characters and extra spaces
        query = re.sub(r'[^\w\s-]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Split into terms and filter out short terms
        terms = [term.lower() for term in query.split() if len(term) >= 2]
        
        return terms
    
    def _apply_filters(self, queryset, filters):
        """Apply various filters to the queryset"""
        
        # Category filter
        categories = filters.get('categories', [])
        if categories:
            queryset = queryset.filter(category__slug__in=categories)
        
        # Brand filter
        brands = filters.get('brands', [])
        if brands:
            queryset = queryset.filter(brand__in=brands)
        
        # Price filters
        price_ranges = filters.get('price_ranges', [])
        if price_ranges:
            price_q = Q()
            for price_range in price_ranges:
                if price_range == '0-25':
                    price_q |= Q(price__lte=25)
                elif price_range == '25-50':
                    price_q |= Q(price__gt=25, price__lte=50)
                elif price_range == '50-100':
                    price_q |= Q(price__gt=50, price__lte=100)
                elif price_range == '100-200':
                    price_q |= Q(price__gt=100, price__lte=200)
                elif price_range == '200+':
                    price_q |= Q(price__gt=200)
            queryset = queryset.filter(price_q)
        
        # Custom price range
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=Decimal(str(min_price)))
            except (ValueError, TypeError):
                pass
        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=Decimal(str(max_price)))
            except (ValueError, TypeError):
                pass
        
        # Rating filter
        min_rating = filters.get('min_rating')
        if min_rating:
            try:
                min_rating = int(min_rating)
                # This would need a subquery to calculate average rating
                # For now, we'll use a simple approximation
                queryset = queryset.annotate(
                    avg_rating=Avg('reviews__rating')
                ).filter(avg_rating__gte=min_rating)
            except (ValueError, TypeError):
                pass
        
        # Availability filter
        availability = filters.get('availability', [])
        if availability:
            if 'in_stock' in availability:
                queryset = queryset.filter(stock__gt=0)
            if 'on_sale' in availability:
                queryset = queryset.filter(original_price__isnull=False, original_price__gt=F('price'))
            if 'featured' in availability:
                queryset = queryset.filter(featured=True)
        
        # Color filter
        colors = filters.get('colors', [])
        if colors:
            queryset = queryset.filter(color__in=colors)
        
        # Size filter
        sizes = filters.get('sizes', [])
        if sizes:
            queryset = queryset.filter(size__in=sizes)
        
        # Material filter
        materials = filters.get('materials', [])
        if materials:
            queryset = queryset.filter(material__in=materials)
        
        # Tag filter
        tags = filters.get('tags', [])
        if tags:
            queryset = queryset.filter(tag_assignments__tag__slug__in=tags)
        
        return queryset.distinct()
    
    def _apply_sorting(self, queryset, sort_by, query):
        """Apply sorting to the queryset"""
        
        if sort_by == 'price-low':
            return queryset.order_by('price', 'name')
        elif sort_by == 'price-high':
            return queryset.order_by('-price', 'name')
        elif sort_by == 'rating':
            # Sort by average rating, then by review count
            return queryset.annotate(
                avg_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            ).order_by('-avg_rating', '-review_count', 'name')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at', 'name')
        elif sort_by == 'oldest':
            return queryset.order_by('created_at', 'name')
        elif sort_by == 'name-asc':
            return queryset.order_by('name')
        elif sort_by == 'name-desc':
            return queryset.order_by('-name')
        elif sort_by == 'brand':
            return queryset.order_by('brand', 'name')
        elif sort_by == 'popularity':
            # Sort by number of orders/interactions
            return queryset.annotate(
                order_count=Count('cartitem__order_items__order', distinct=True)
            ).order_by('-order_count', '-featured', 'name')
        else:  # relevance (default)
            if query and hasattr(queryset.model, 'relevance_score'):
                return queryset.order_by('-relevance_score', '-featured', '-created_at')
            else:
                return queryset.order_by('-featured', '-created_at', 'name')
    
    def _get_filter_options(self, queryset, query, applied_filters):
        """Get available filter options based on current search results"""
        
        # Get unique categories with product counts
        categories = Category.objects.filter(
            products__in=queryset,
            is_active=True
        ).annotate(
            product_count=Count('products', distinct=True)
        ).order_by('name')
        
        # Get unique brands with product counts
        brands = queryset.values('brand').exclude(brand='').annotate(
            product_count=Count('id')
        ).order_by('brand')
        
        # Get price range statistics
        price_stats = queryset.aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
            avg_price=Avg('price')
        )
        
        # Set defaults if no products found
        price_stats['min_price'] = price_stats['min_price'] or 0
        price_stats['max_price'] = price_stats['max_price'] or 1000
        price_stats['avg_price'] = price_stats['avg_price'] or 50
        
        # Get available colors
        colors = queryset.exclude(color='').values_list('color', flat=True).distinct().order_by('color')
        
        # Get available sizes
        sizes = queryset.exclude(size='').values_list('size', flat=True).distinct().order_by('size')
        
        # Get available materials
        materials = queryset.exclude(material='').values_list('material', flat=True).distinct().order_by('material')
        
        # Get available tags
        tags = ProductTag.objects.filter(
            product_assignments__product__in=queryset,
            is_active=True
        ).annotate(
            product_count=Count('product_assignments', distinct=True)
        ).order_by('name')
        
        return {
            'categories': categories,
            'brands': brands,
            'price_stats': price_stats,
            'colors': colors,
            'sizes': sizes,
            'materials': materials,
            'tags': tags,
        }
    
    def log_search(self, query, user=None, session_key=None, ip_address=None, 
                   user_agent='', filters=None, results_count=0):
        """Log search query for analytics"""
        try:
            # Create search query record
            search_record = SearchQueryModel.objects.create(
                query=query,
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                category_filter=','.join(filters.get('categories', [])) if filters else '',
                price_filter=','.join(filters.get('price_ranges', [])) if filters else '',
                brand_filter=','.join(filters.get('brands', [])) if filters else '',
                results_count=results_count,
            )
            
            # Update popular searches
            if query.strip():
                popular_search, created = PopularSearch.objects.get_or_create(
                    query=query.strip().lower(),
                    defaults={'search_count': 1}
                )
                if not created:
                    popular_search.search_count = F('search_count') + 1
                    popular_search.save(update_fields=['search_count', 'last_searched'])
            
            return search_record
        except Exception as e:
            # Don't let search logging break the search functionality
            print(f"Error logging search: {e}")
            return None
    
    def get_search_suggestions(self, query, limit=10):
        """Get search suggestions based on popular searches and product names"""
        if len(query) < 2:
            return []
        
        suggestions = set()
        
        # Get popular searches that start with or contain the query
        popular_searches = PopularSearch.objects.filter(
            Q(query__istartswith=query.lower()) | Q(query__icontains=query.lower())
        )[:limit * 2]
        
        for search in popular_searches:
            suggestions.add(search.query)
        
        # Get product names that match
        products = Product.objects.filter(
            Q(name__istartswith=query) | Q(name__icontains=query),
            available=True
        ).values_list('name', flat=True)[:limit]
        
        for product_name in products:
            suggestions.add(product_name.lower())
        
        # Get brand names that match
        brands = Product.objects.filter(
            brand__istartswith=query,
            available=True
        ).values_list('brand', flat=True).distinct()[:limit//2]
        
        for brand in brands:
            if brand:
                suggestions.add(brand.lower())
        
        return sorted(list(suggestions))[:limit]


# Utility functions for template use
def get_sort_options():
    """Get available sorting options for templates"""
    return [
        ('relevance', 'Relevance'),
        ('price-low', 'Price: Low to High'),
        ('price-high', 'Price: High to Low'),
        ('rating', 'Customer Rating'),
        ('newest', 'Newest First'),
        ('oldest', 'Oldest First'),
        ('name-asc', 'Name: A to Z'),
        ('name-desc', 'Name: Z to A'),
        ('brand', 'Brand'),
        ('popularity', 'Popularity'),
    ]


def get_price_ranges():
    """Get predefined price ranges for filters"""
    return [
        ('0-25', 'Under $25'),
        ('25-50', '$25 to $50'),
        ('50-100', '$50 to $100'),
        ('100-200', '$100 to $200'),
        ('200+', '$200 & Above'),
    ]


def get_rating_options():
    """Get rating filter options"""
    return [
        (4, '4 Stars & Up'),
        (3, '3 Stars & Up'),
        (2, '2 Stars & Up'),
        (1, '1 Star & Up'),
    ]


# Initialize global search manager instance
search_manager = SearchManager()