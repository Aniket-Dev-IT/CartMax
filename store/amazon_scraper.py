"""
Real Amazon Price Scraper for CartMax
IMPORTANT: Use responsibly and respect robots.txt and rate limits
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import quote_plus
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AmazonPriceScraper:
    """
    Responsible Amazon price scraper with rate limiting and caching
    """
    
    def __init__(self):
        self.session = requests.Session()
        
        # Rotate User-Agents to appear more natural
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.last_request_time = 0
        self.min_delay = 2  # Minimum 2 seconds between requests
    
    def _get_headers(self):
        """Get random headers for the request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last + random.uniform(1, 3)
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_amazon_india(self, query, max_results=5):
        """
        Search Amazon India for products and extract prices
        """
        cache_key = f'amazon_in_search_{hash(query.lower())}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Using cached Amazon India results for: {query}")
            return cached_result
        
        try:
            self._rate_limit()
            
            search_url = f"https://www.amazon.in/s?k={quote_plus(query)}&ref=nb_sb_noss"
            
            response = self.session.get(
                search_url, 
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Amazon India search failed with status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = self._parse_amazon_india_results(soup, max_results)
            
            # Cache for 4 hours
            cache.set(cache_key, products, 14400)
            
            logger.info(f"Found {len(products)} products on Amazon India for '{query}'")
            return products
            
        except Exception as e:
            logger.error(f"Amazon India scraping failed: {e}")
            return []
    
    def _parse_amazon_india_results(self, soup, max_results=5):
        """Parse Amazon India search results"""
        products = []
        
        # Amazon India uses specific selectors for search results
        product_containers = soup.find_all('div', {
            'data-component-type': 's-search-result'
        })[:max_results]
        
        for container in product_containers:
            try:
                product_data = self._extract_amazon_india_product(container)
                if product_data:
                    products.append(product_data)
            except Exception as e:
                logger.debug(f"Failed to parse product container: {e}")
                continue
        
        return products
    
    def _extract_amazon_india_product(self, container):
        """Extract product data from Amazon India container"""
        try:
            # Product title - try multiple selectors
            title_element = container.find('h2')
            if not title_element:
                title_element = container.find('span', class_=re.compile('s-.*-color'))
            if not title_element:
                title_element = container.find('a')
            
            if not title_element:
                return None
                
            title = title_element.get_text().strip()
            if len(title) < 3:
                return None
            
            # Price extraction - multiple methods
            price = None
            
            # Method 1: a-price-whole and a-price-fraction
            price_container = container.find('span', class_='a-price-whole')
            if price_container:
                price_text = price_container.get_text().strip().replace(',', '').replace('₹', '').strip()
                price_decimal = container.find('span', class_='a-price-fraction')
                if price_decimal:
                    price_text += '.' + price_decimal.get_text().strip()
                try:
                    price = float(price_text)
                except ValueError:
                    price = None
            
            # Method 2: Look for price in any span
            if not price:
                for span in container.find_all('span', class_=re.compile('a-price')):
                    text = span.get_text().strip().replace(',', '').replace('₹', '').strip()
                    if text and text[0].isdigit():
                        try:
                            price = float(text.split()[0])
                            break
                        except (ValueError, IndexError):
                            continue
            
            if not price or price <= 0:
                return None
            
            # Rating
            rating_element = container.find('span', class_='a-icon-alt')
            rating = None
            if rating_element:
                rating_text = rating_element.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Review count
            reviews_count = 0
            for elem in container.find_all(['a', 'span']):
                text = elem.get_text()
                if 'rating' in text.lower() or 'review' in text.lower():
                    match = re.search(r'(\d+(?:,\d+)*)', text)
                    if match:
                        reviews_count = int(match.group(1).replace(',', ''))
                        break
            
            return {
                'title': title,
                'price': price,
                'currency': 'INR',
                'rating': rating,
                'reviews_count': reviews_count,
                'source': 'Amazon India',
                'availability': 'in_stock'
            }
            
        except Exception as e:
            logger.debug(f"Failed to extract Amazon India product: {e}")
            return None
    
    def search_amazon_us(self, query, max_results=5):
        """Search Amazon US for products and extract prices"""
        cache_key = f'amazon_us_search_{hash(query.lower())}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Using cached Amazon US results for: {query}")
            return cached_result
        
        try:
            self._rate_limit()
            
            search_url = f"https://www.amazon.com/s?k={quote_plus(query)}&ref=nb_sb_noss"
            
            response = self.session.get(
                search_url, 
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Amazon US search failed with status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = self._parse_amazon_us_results(soup, max_results)
            
            # Cache for 4 hours
            cache.set(cache_key, products, 14400)
            
            logger.info(f"Found {len(products)} products on Amazon US for '{query}'")
            return products
            
        except Exception as e:
            logger.error(f"Amazon US scraping failed: {e}")
            return []
    
    def _parse_amazon_us_results(self, soup, max_results=5):
        """Parse Amazon US search results"""
        products = []
        
        product_containers = soup.find_all('div', {
            'data-component-type': 's-search-result'
        })[:max_results]
        
        for container in product_containers:
            try:
                product_data = self._extract_amazon_us_product(container)
                if product_data:
                    products.append(product_data)
            except Exception as e:
                logger.debug(f"Failed to parse US product container: {e}")
                continue
        
        return products
    
    def _extract_amazon_us_product(self, container):
        """Extract product data from Amazon US container"""
        try:
            # Product title - try multiple selectors
            title_element = container.find('h2')
            if not title_element:
                title_element = container.find('span', class_=re.compile('s-.*-color'))
            if not title_element:
                title_element = container.find('a')
            
            if not title_element:
                return None
                
            title = title_element.get_text().strip()
            if len(title) < 3:
                return None
            
            # Price extraction - multiple methods
            price = None
            
            # Method 1: a-price-whole and a-price-fraction
            price_container = container.find('span', class_='a-price-whole')
            if price_container:
                price_text = price_container.get_text().strip().replace(',', '').replace('$', '').strip()
                price_decimal = container.find('span', class_='a-price-fraction')
                if price_decimal:
                    price_text += '.' + price_decimal.get_text().strip()
                try:
                    price = float(price_text)
                except ValueError:
                    price = None
            
            # Method 2: Look for price in any span
            if not price:
                for span in container.find_all('span', class_=re.compile('a-price')):
                    text = span.get_text().strip().replace(',', '').replace('$', '').strip()
                    if text and text[0].isdigit():
                        try:
                            price = float(text.split()[0])
                            break
                        except (ValueError, IndexError):
                            continue
            
            if not price or price <= 0:
                return None
            
            # Rating
            rating_element = container.find('span', class_='a-icon-alt')
            rating = None
            if rating_element:
                rating_text = rating_element.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Review count
            reviews_count = 0
            for elem in container.find_all(['a', 'span']):
                text = elem.get_text()
                if 'rating' in text.lower() or 'review' in text.lower():
                    match = re.search(r'(\d+(?:,\d+)*)', text)
                    if match:
                        reviews_count = int(match.group(1).replace(',', ''))
                        break
            
            return {
                'title': title,
                'price': price,
                'currency': 'USD',
                'rating': rating,
                'reviews_count': reviews_count,
                'source': 'Amazon US',
                'availability': 'in_stock'
            }
            
        except Exception as e:
            logger.debug(f"Failed to extract Amazon US product: {e}")
            return None
    
    def get_product_price_by_asin(self, asin, region='in'):
        """
        Get specific product price by ASIN (Amazon Standard Identification Number)
        More accurate for known products
        """
        if region == 'in':
            url = f"https://www.amazon.in/dp/{asin}"
            cache_key = f'amazon_in_asin_{asin}'
        else:
            url = f"https://www.amazon.com/dp/{asin}"
            cache_key = f'amazon_us_asin_{asin}'
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            self._rate_limit()
            
            response = self.session.get(
                url, 
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract price from product page
            price_element = soup.find('span', class_='a-price-whole')
            if not price_element:
                return None
            
            price_text = price_element.get_text().strip().replace(',', '')
            price_decimal = soup.find('span', class_='a-price-fraction')
            if price_decimal:
                price_text += '.' + price_decimal.get_text().strip()
            
            price = float(price_text)
            
            # Cache for 2 hours (specific product prices change less frequently)
            result = {
                'asin': asin,
                'price': price,
                'currency': 'INR' if region == 'in' else 'USD',
                'source': f'Amazon {region.upper()}',
                'timestamp': time.time()
            }
            
            cache.set(cache_key, result, 7200)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get price for ASIN {asin}: {e}")
            return None

# Global instance
amazon_scraper = AmazonPriceScraper()

# Usage example and testing function
def test_amazon_scraper():
    """Test the Amazon scraper with a sample product"""
    test_queries = [
        "mamaearth vitamin c face serum",
        "iphone 13",
        "samsung galaxy",
        "nike shoes"
    ]
    
    scraper = AmazonPriceScraper()
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        
        # Test Amazon India
        in_results = scraper.search_amazon_india(query, max_results=3)
        print(f"📱 Amazon India: {len(in_results)} results")
        for result in in_results[:2]:
            print(f"   ₹{result['price']} - {result['title'][:50]}...")
        
        # Test Amazon US
        us_results = scraper.search_amazon_us(query, max_results=3)
        print(f"🇺🇸 Amazon US: {len(us_results)} results")
        for result in us_results[:2]:
            print(f"   ${result['price']} - {result['title'][:50]}...")

if __name__ == '__main__':
    test_amazon_scraper()