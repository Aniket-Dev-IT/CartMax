"""
Utility functions for CartMax
"""

def get_currency_by_country(country):
    """
    Get currency code based on country.
    Rule: India → INR, All other countries → USD
    This is the single source of truth for currency determination.
    """
    if country and country.lower() == 'india':
        return 'INR'
    return 'USD'


def get_exchange_rate(from_currency='USD', to_currency='INR'):
    """
    Get exchange rate between two currencies.
    Currently uses fixed rates for USD ↔ INR conversion.
    Can be updated to fetch from API in future.
    """
    rates = {
        ('USD', 'INR'): 83.0,  # 1 USD = 83 INR (can be updated)
        ('INR', 'USD'): 1 / 83.0,  # 1 INR = 0.012 USD
    }
    
    key = (from_currency.upper(), to_currency.upper())
    return rates.get(key, 1.0)  # Default to 1.0 if no rate found


def get_user_currency(user):
    """
    Get the correct currency for a user based on their preferred currency setting.
    Falls back to country-based detection if not set.
    This is the definitive way to get user's currency.
    """
    if not user.is_authenticated:
        return 'USD'  # Default for anonymous users
    
    try:
        profile = user.profile
        
        # First priority: Use explicitly set preferred_currency
        if hasattr(profile, 'preferred_currency') and profile.preferred_currency:
            return profile.preferred_currency
        
        # Second priority: Determine from country
        country = profile.country or 'United States'
        return get_currency_by_country(country)
    except:
        return 'USD'  # Fallback
