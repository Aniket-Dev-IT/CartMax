# 📡 CartMax API Documentation

Complete API reference for CartMax e-commerce platform.

---

## 🔑 Authentication

### Session-Based Authentication
CartMax uses Django session-based authentication.

**Login:**
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "user_id": 1,
  "username": "user@example.com",
  "message": "Login successful"
}
```

### Logout
```http
POST /api/auth/logout/
```

---

## 🛍️ Product Endpoints

### Get All Products
```http
GET /api/products/
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `category`: Filter by category ID
- `search`: Search by product name
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `sort`: Sort by (name, price, rating)

**Response:**
```json
{
  "count": 100,
  "next": "/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Product Name",
      "description": "Product description",
      "price_inr": 9999,
      "price_usd": 120,
      "category": "Electronics",
      "in_stock": true,
      "rating": 4.5,
      "image": "url_to_image"
    }
  ]
}
```

### Get Single Product
```http
GET /api/products/{product_id}/
```

**Response:**
```json
{
  "id": 1,
  "name": "iPhone 14 Pro",
  "description": "Latest Apple smartphone",
  "price_inr": 99999,
  "price_usd": 1200,
  "category": "Electronics",
  "brand": "Apple",
  "sku": "IPHONE14PRO",
  "stock": 15,
  "images": ["url1", "url2"],
  "rating": 4.7,
  "reviews_count": 128,
  "specifications": {
    "storage": "256GB",
    "color": "Space Black"
  }
}
```

### Search Products
```http
GET /api/products/search/?q=laptop
```

**Response:** Similar to Get All Products

---

## 🛒 Shopping Cart Endpoints

### Get Cart
```http
GET /api/cart/
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "items": [
    {
      "id": 1,
      "product_id": 5,
      "product_name": "Laptop",
      "quantity": 1,
      "price": 74999,
      "subtotal": 74999
    }
  ],
  "subtotal": 74999,
  "tax": 13500,
  "total": 88499,
  "currency": "INR"
}
```

### Add to Cart
```http
POST /api/cart/add/
Content-Type: application/json

{
  "product_id": 5,
  "quantity": 1
}
```

### Update Cart Item
```http
PUT /api/cart/items/{item_id}/
Content-Type: application/json

{
  "quantity": 2
}
```

### Remove from Cart
```http
DELETE /api/cart/items/{item_id}/
```

### Clear Cart
```http
DELETE /api/cart/clear/
```

---

## 💳 Order Endpoints

### Create Order
```http
POST /api/orders/
Content-Type: application/json

{
  "shipping_address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA"
  },
  "payment_method": "credit_card",
  "coupon_code": "SAVE10"
}
```

**Response:**
```json
{
  "id": "ORD-2025-001",
  "user_id": 1,
  "order_date": "2025-10-27T09:00:00Z",
  "status": "pending",
  "items": [...],
  "subtotal": 74999,
  "tax": 13500,
  "discount": 7500,
  "total": 80999,
  "currency": "INR"
}
```

### Get Order History
```http
GET /api/orders/
```

**Response:** Array of orders

### Get Single Order
```http
GET /api/orders/{order_id}/
```

### Cancel Order
```http
PUT /api/orders/{order_id}/cancel/
```

---

## ⭐ Review & Rating Endpoints

### Get Product Reviews
```http
GET /api/products/{product_id}/reviews/
```

**Response:**
```json
{
  "count": 128,
  "average_rating": 4.5,
  "reviews": [
    {
      "id": 1,
      "user": "John Doe",
      "rating": 5,
      "title": "Excellent product",
      "comment": "Very satisfied with this purchase",
      "helpful_votes": 24,
      "date": "2025-10-20T14:30:00Z"
    }
  ]
}
```

### Post Review
```http
POST /api/products/{product_id}/reviews/
Content-Type: application/json

{
  "rating": 5,
  "title": "Great product",
  "comment": "Exactly what I was looking for"
}
```

---

## 🔖 Coupon Endpoints

### Validate Coupon
```http
POST /api/coupons/validate/
Content-Type: application/json

{
  "code": "SAVE10"
}
```

**Response:**
```json
{
  "valid": true,
  "discount_type": "percentage",
  "discount_value": 10,
  "description": "10% off on all items"
}
```

### Apply Coupon
```http
POST /api/coupons/apply/
Content-Type: application/json

{
  "code": "SAVE10"
}
```

---

## 👤 User Profile Endpoints

### Get Profile
```http
GET /api/user/profile/
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-234-567-8900",
  "currency_preference": "USD",
  "addresses": [...],
  "created_at": "2025-10-01T10:00:00Z"
}
```

### Update Profile
```http
PUT /api/user/profile/
Content-Type: application/json

{
  "first_name": "Jane",
  "phone": "+1-234-567-8901",
  "currency_preference": "INR"
}
```

### Add Address
```http
POST /api/user/addresses/
Content-Type: application/json

{
  "type": "shipping",
  "street": "456 Oak Ave",
  "city": "Boston",
  "state": "MA",
  "postal_code": "02101",
  "country": "USA",
  "is_default": false
}
```

---

## 💰 Pricing & Currency

### Get Exchange Rates
```http
GET /api/currency/rates/
```

**Response:**
```json
{
  "base": "USD",
  "rates": {
    "INR": 83.12,
    "EUR": 0.92,
    "GBP": 0.79
  },
  "timestamp": "2025-10-27T09:00:00Z"
}
```

### Convert Price
```http
GET /api/currency/convert/?amount=100&from=USD&to=INR
```

**Response:**
```json
{
  "amount": 100,
  "from": "USD",
  "to": "INR",
  "converted_amount": 8312,
  "rate": 83.12
}
```

---

## 📊 Admin Endpoints

### Get Dashboard Stats
```http
GET /api/admin/stats/
```

**Response:**
```json
{
  "total_sales": 500000,
  "total_orders": 256,
  "active_users": 1200,
  "products_count": 100,
  "low_stock_items": 5
}
```

### Get Sales Report
```http
GET /api/admin/reports/sales/?start_date=2025-01-01&end_date=2025-10-27
```

---

## 🔍 Wishlist Endpoints

### Get Wishlist
```http
GET /api/wishlist/
```

### Add to Wishlist
```http
POST /api/wishlist/add/
Content-Type: application/json

{
  "product_id": 5
}
```

### Remove from Wishlist
```http
DELETE /api/wishlist/remove/{product_id}/
```

---

## 🔄 Product Recommendation Endpoints

### Get Recommendations
```http
GET /api/products/{product_id}/recommendations/
```

**Query Parameters:**
- `type`: similar, frequently_bought_together, popular
- `limit`: Number of recommendations (max: 10)

**Response:**
```json
{
  "type": "similar",
  "products": [
    {
      "id": 6,
      "name": "Related Product",
      "price": 79999,
      "relevance": 0.95
    }
  ]
}
```

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "details": "Missing required field: product_id"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "message": "Please log in to access this resource"
}
```

### 403 Forbidden
```json
{
  "error": "Permission denied",
  "message": "You don't have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "message": "Product with ID 999 not found"
}
```

### 500 Server Error
```json
{
  "error": "Server error",
  "message": "An unexpected error occurred. Please try again."
}
```

---

## 📋 Rate Limiting

- **Anonymous Users:** 100 requests/hour
- **Authenticated Users:** 1000 requests/hour
- **Admin Users:** 10000 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1635340800
```

---

## 🔐 Security Notes

1. **Always use HTTPS** in production
2. **Never expose API tokens** in client-side code
3. **Validate all inputs** on the server side
4. **Use CORS** properly for cross-origin requests
5. **Implement rate limiting** to prevent abuse
6. **Log suspicious activities** for audit trails

---

## 📚 More Resources

- [Full Documentation](README.md)
- [Features Guide](FEATURES.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

**Last Updated:** October 27, 2025  
**API Version:** 1.0.0
