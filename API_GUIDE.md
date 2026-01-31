# API Guide - Zero Waste Management System

## Base URL
```
http://127.0.0.1:5000
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Authentication Endpoints

### 1. Register User
**POST** `/api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe",
  "role": "CITIZEN",
  "phone": "+8801234567890"
}
```

**Roles:** `CITIZEN`, `CLEANER`, `ADMIN`

**Response (201):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "CITIZEN",
    "phone": "+8801234567890",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

### 2. Login
**POST** `/api/auth/login`

Login and receive JWT token.

**Request Body:**
```json
{
  "email": "citizen1@test.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "citizen1@test.com",
    "name": "Rahim Ahmed",
    "role": "CITIZEN",
    "is_active": true
  }
}
```

**Save the token** - You'll need it for all protected endpoints!

---

### 3. Get Current User
**GET** `/api/auth/me`

Get current authenticated user with profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "citizen1@test.com",
      "name": "Rahim Ahmed",
      "role": "CITIZEN"
    },
    "profile": {
      "id": "uuid",
      "user_id": "uuid",
      "green_points_balance": 250,
      "total_reports": 15,
      "approved_reports": 12,
      "current_streak": 5,
      "rank": 3
    }
  }
}
```

---

## Citizen Endpoints

### 1. Get Citizen Profile
**GET** `/api/citizen/profile`

Get citizen profile with statistics.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "citizen1@test.com",
      "name": "Rahim Ahmed",
      "phone": "+8801234567890",
      "role": "CITIZEN",
      "avatar_url": "https://...",
      "dark_mode": false
    },
    "profile": {
      "id": "uuid",
      "user_id": "uuid",
      "green_points_balance": 250,
      "total_reports": 15,
      "approved_reports": 12,
      "current_streak": 5,
      "longest_streak": 10,
      "rank": 3,
      "badges_count": 4
    }
  }
}
```

---

### 2. Update Citizen Profile
**PUT** `/api/citizen/profile`

Update citizen user details.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Request Body:**
```json
{
  "name": "Rahim Ahmed Updated",
  "phone": "+8801987654321",
  "avatar_url": "https://new-avatar.com/image.jpg",
  "dark_mode": true,
  "email_notifications": false
}
```

**Allowed Fields:**
- `name` - User's name
- `phone` - Phone number
- `avatar_url` - Profile picture URL
- `address` - Address
- `language` - Language preference (e.g., 'en', 'bn')
- `email_notifications` - Email notification preference (boolean)
- `push_notifications` - Push notification preference (boolean)
- `dark_mode` - Dark mode preference (boolean)

**Response (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "user": { ... },
    "profile": { ... }
  }
}
```

---

### 3. Get Citizen Stats
**GET** `/api/citizen/stats`

Get detailed citizen statistics.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "green_points_balance": 250,
    "total_reports": 15,
    "approved_reports": 12,
    "pending_reports": 2,
    "completed_reports": 10,
    "current_streak": 5,
    "longest_streak": 10,
    "rank": 3,
    "total_badges": 4,
    "reviews_given": 8
  }
}
```

---

## Cleaner Endpoints

### 1. Get Cleaner Profile
**GET** `/api/cleaner/profile`

Get cleaner profile with statistics.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "cleaner1@test.com",
      "name": "Abdul Karim",
      "phone": "+8801234567890",
      "role": "CLEANER"
    },
    "profile": {
      "id": "uuid",
      "user_id": "uuid",
      "total_earnings": 25000.00,
      "pending_earnings": 1500.00,
      "completed_tasks": 35,
      "current_tasks": 2,
      "rating": 4.75,
      "total_ratings": 28,
      "total_reviews": 28
    }
  }
}
```

---

### 2. Update Cleaner Profile
**PUT** `/api/cleaner/profile`

Update cleaner user details.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Request Body:**
```json
{
  "name": "Abdul Karim Updated",
  "phone": "+8801987654321",
  "avatar_url": "https://new-avatar.com/image.jpg"
}
```

**Allowed Fields:** Same as citizen profile

**Response (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "user": { ... },
    "profile": { ... }
  }
}
```

---

### 3. Get Cleaner Stats
**GET** `/api/cleaner/stats`

Get detailed cleaner statistics.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_earnings": 25000.00,
    "pending_earnings": 1500.00,
    "completed_tasks": 35,
    "current_tasks": 2,
    "active_tasks": 2,
    "rating": 4.75,
    "total_ratings": 28,
    "total_reviews": 28,
    "average_review_rating": 4.68,
    "pending_amount": 1500.00,
    "paid_amount": 23500.00
  }
}
```

---

## Admin Endpoints

### 1. Get Admin Profile
**GET** `/api/admin/profile`

Get admin profile.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "admin1@test.com",
      "name": "Dr. Mahmud Hasan",
      "role": "ADMIN"
    },
    "profile": {
      "id": "uuid",
      "user_id": "uuid",
      "department": "Waste Management",
      "role_title": "Senior Officer"
    }
  }
}
```

---

### 2. Update Admin Profile
**PUT** `/api/admin/profile`

Update admin user details and profile.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "name": "Dr. Mahmud Hasan Updated",
  "phone": "+8801987654321",
  "department": "Environmental Services",
  "role_title": "Department Head"
}
```

**Allowed Fields:**
- User fields: Same as citizen/cleaner
- Profile fields: `department`, `role_title`

**Response (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "user": { ... },
    "profile": { ... }
  }
}
```

---

### 3. Get All Users
**GET** `/api/admin/users`

Get all users with filtering (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `role` - Filter by role (CITIZEN, CLEANER, ADMIN)
- `is_active` - Filter by active status (true/false)
- `limit` - Limit results (default: all)
- `offset` - Offset for pagination (default: 0)

**Examples:**
```
GET /api/admin/users?role=CITIZEN&limit=10
GET /api/admin/users?is_active=true&limit=20&offset=20
```

**Response (200):**
```json
{
  "success": true,
  "total": 23,
  "count": 10,
  "data": [
    {
      "id": "uuid",
      "email": "citizen1@test.com",
      "name": "Rahim Ahmed",
      "phone": "+8801234567890",
      "role": "CITIZEN",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "last_login_at": "2024-01-15T10:30:00"
    }
  ]
}
```

---

### 4. Get User Details
**GET** `/api/admin/users/<user_id>`

Get detailed information about a specific user (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "citizen1@test.com",
      "name": "Rahim Ahmed",
      "role": "CITIZEN",
      "is_active": true
    },
    "profile": {
      "green_points_balance": 250,
      "total_reports": 15,
      "approved_reports": 12,
      "badges_count": 4,
      "total_reports_count": 15
    }
  }
}
```

---

### 5. Get System Stats
**GET** `/api/admin/stats`

Get system-wide statistics (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_citizens": 12,
    "total_cleaners": 8,
    "total_admins": 3,
    "total_reports": 50,
    "pending_reports": 10,
    "completed_reports": 25,
    "total_tasks": 15,
    "available_tasks": 5,
    "total_zones": 5,
    "avg_zone_cleanliness": 82.5,
    "open_alerts": 3
  }
}
```

---

## Health Check

### Check API Health
**GET** `/api/health`

Check if API and database are running.

**Response (200):**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Content-Type must be application/json"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Token is missing"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "User not found"
}
```

### 409 Conflict
```json
{
  "success": false,
  "error": "Email already exists"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## Testing with cURL

### Register
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User",
    "role": "CITIZEN"
  }'
```

### Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "citizen1@test.com",
    "password": "password123"
  }'
```

### Get Profile (with token)
```bash
curl -X GET http://127.0.0.1:5000/api/citizen/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Update Profile
```bash
curl -X PUT http://127.0.0.1:5000/api/citizen/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "dark_mode": true
  }'
```

---

## Testing with Postman

1. **Import Collection**: Create a new collection "Zero Waste API"
2. **Set Base URL**: Create environment variable `base_url = http://127.0.0.1:5000`
3. **Login**: POST to `/api/auth/login` and save token
4. **Set Token**: Add to collection authorization: Bearer Token
5. **Test Endpoints**: Use saved token for all protected routes

---

## Test Credentials

### Citizens
```
Email: citizen1@test.com to citizen12@test.com
Password: password123
```

### Cleaners
```
Email: cleaner1@test.com to cleaner8@test.com
Password: password123
```

### Admins
```
Email: admin1@test.com to admin3@test.com
Password: admin123
```

---

**Happy Testing!** 🚀
