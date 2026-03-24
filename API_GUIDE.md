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

### 4. Logout
**POST** `/api/auth/logout`

Logout and invalidate current session.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
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

### 4. Submit Report
**POST** `/api/citizen/reports`

Submit a new waste report.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Request Body:**
```json
{
  "zone_id": "zone-uuid",
  "description": "Overflowing garbage bin near the park entrance",
  "image_url": "https://example.com/waste-image.jpg",
  "severity": "MEDIUM",
  "latitude": 23.8103,
  "longitude": 90.4125
}
```

**Severity Levels:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

**Response (201):**
```json
{
  "success": true,
  "message": "Report submitted successfully",
  "data": {
    "id": "report-uuid",
    "zone_id": "zone-uuid",
    "description": "Overflowing garbage bin near the park entrance",
    "severity": "MEDIUM",
    "status": "SUBMITTED",
    "created_at": "2024-01-01T10:30:00",
    "points_earned": 15
  }
}
```

---

### 5. Get My Reports
**GET** `/api/citizen/reports`

Get all reports submitted by the citizen.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Query Parameters:**
- `status` - Filter by status (SUBMITTED, APPROVED, DECLINED, IN_PROGRESS, COMPLETED)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 15,
  "count": 10,
  "data": [
    {
      "id": "report-uuid",
      "zone_name": "Dhanmondi Park",
      "description": "Overflowing garbage bin",
      "severity": "MEDIUM",
      "status": "COMPLETED",
      "image_url": "https://...",
      "after_image_url": "https://...",
      "created_at": "2024-01-01T10:30:00",
      "completed_at": "2024-01-02T15:45:00",
      "cleaner_name": "Abdul Karim"
    }
  ]
}
```

---

### 6. Get Report Details
**GET** `/api/citizen/reports/<report_id>`

Get detailed information about a specific report.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "report": {
      "id": "report-uuid",
      "description": "Overflowing garbage bin",
      "severity": "MEDIUM",
      "status": "COMPLETED",
      "image_url": "https://...",
      "after_image_url": "https://...",
      "created_at": "2024-01-01T10:30:00",
      "completed_at": "2024-01-02T15:45:00"
    },
    "zone": {
      "id": "zone-uuid",
      "name": "Dhanmondi Park",
      "cleanliness_score": 85
    },
    "cleaner": {
      "id": "cleaner-uuid",
      "name": "Abdul Karim",
      "rating": 4.5
    },
    "ai_analysis": {
      "description": "Mixed waste including plastic bottles and food waste",
      "estimated_volume": "2-3 cubic meters",
      "environmental_impact": "MODERATE",
      "health_hazard": true,
      "recommended_action": "Immediate cleanup required"
    },
    "cleanup_comparison": {
      "completion_percentage": 95,
      "quality_rating": "EXCELLENT",
      "environmental_benefit": "Significant improvement in area cleanliness"
    }
  }
}
```

---

### 7. Submit Cleanup Review
**POST** `/api/citizen/reports/<report_id>/review`

Submit a review for completed cleanup work.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Request Body:**
```json
{
  "rating": 5,
  "comment": "Excellent work! The area is completely clean now."
}
```

**Rating:** 1-5 stars

**Response (201):**
```json
{
  "success": true,
  "message": "Review submitted successfully",
  "data": {
    "rating": 5,
    "comment": "Excellent work! The area is completely clean now.",
    "points_earned": 5
  }
}
```

---

### 8. Get My Badges
**GET** `/api/citizen/badges`

Get all badges earned by the citizen.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "badge-uuid",
      "name": "First Step",
      "description": "Submitted your first waste report",
      "icon": "🌱",
      "earned_at": "2024-01-01T10:30:00"
    },
    {
      "id": "badge-uuid",
      "name": "Eco Warrior",
      "description": "Had 10 reports approved",
      "icon": "🌿",
      "earned_at": "2024-01-15T14:20:00"
    }
  ]
}
```

---

### 9. Get Green Points History
**GET** `/api/citizen/points`

Get green points transaction history.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Query Parameters:**
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 25,
  "current_balance": 250,
  "data": [
    {
      "id": "transaction-uuid",
      "green_points": 25,
      "reason": "Report approved",
      "report_id": "report-uuid",
      "created_at": "2024-01-01T10:30:00"
    },
    {
      "id": "transaction-uuid",
      "green_points": 15,
      "reason": "Report submitted",
      "report_id": "report-uuid",
      "created_at": "2024-01-01T10:30:00"
    }
  ]
}
```

---

### 10. Get Leaderboard
**GET** `/api/citizen/leaderboard`

Get citizen leaderboard rankings.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Query Parameters:**
- `period` - Time period (all_time, month, week) - default: all_time
- `limit` - Limit results (default: 10)

**Response (200):**
```json
{
  "success": true,
  "period": "all_time",
  "my_rank": 3,
  "data": [
    {
      "rank": 1,
      "user_name": "Fatima Khan",
      "avatar_url": "https://...",
      "total_green_points": 1250,
      "approved_reports": 45,
      "badges_count": 6
    },
    {
      "rank": 2,
      "user_name": "Mohammad Ali",
      "avatar_url": "https://...",
      "total_green_points": 980,
      "approved_reports": 38,
      "badges_count": 5
    }
  ]
}
```

---

### 11. Get Notifications
**GET** `/api/citizen/notifications`

Get user notifications.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Query Parameters:**
- `is_read` - Filter by read status (true/false)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "unread_count": 3,
  "data": [
    {
      "id": "notification-uuid",
      "type": "REPORT",
      "title": "Report Approved!",
      "message": "Your waste report has been approved! You earned 25 bonus points.",
      "is_read": false,
      "related_report_id": "report-uuid",
      "created_at": "2024-01-01T10:30:00"
    }
  ]
}
```

---

### 12. Mark Notification as Read
**PUT** `/api/citizen/notifications/<notification_id>/read`

Mark a notification as read.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

---

### 13. Mark All Notifications as Read
**PUT** `/api/citizen/notifications/read-all`

Mark all notifications as read.

**Headers:**
```
Authorization: Bearer <citizen_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "All notifications marked as read"
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

### 4. Get Available Tasks
**GET** `/api/cleaner/tasks/available`

Get all available tasks that can be taken.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Query Parameters:**
- `zone_id` - Filter by zone
- `priority` - Filter by priority (LOW, MEDIUM, HIGH, CRITICAL)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 15,
  "data": [
    {
      "id": "task-uuid",
      "zone_name": "Dhanmondi Park",
      "description": "Clean overflowing garbage bin near park entrance",
      "priority": "HIGH",
      "due_date": "2024-01-05T23:59:59",
      "reward": 500.00,
      "report": {
        "id": "report-uuid",
        "image_url": "https://...",
        "severity": "HIGH",
        "reporter_name": "Rahim Ahmed"
      },
      "ai_analysis": {
        "estimated_volume": "2-3 cubic meters",
        "estimated_cleanup_time": "2-3 hours",
        "special_equipment": ["Gloves", "Waste bags", "Broom"]
      }
    }
  ]
}
```

---

### 5. Take Task
**POST** `/api/cleaner/tasks/<task_id>/take`

Take an available task.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Task taken successfully",
  "data": {
    "id": "task-uuid",
    "status": "IN_PROGRESS",
    "taken_at": "2024-01-01T10:30:00"
  }
}
```

---

### 6. Get My Tasks
**GET** `/api/cleaner/tasks`

Get all tasks assigned to the cleaner.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Query Parameters:**
- `status` - Filter by status (IN_PROGRESS, COMPLETED)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 37,
  "data": [
    {
      "id": "task-uuid",
      "zone_name": "Dhanmondi Park",
      "description": "Clean overflowing garbage bin",
      "priority": "HIGH",
      "status": "IN_PROGRESS",
      "reward": 500.00,
      "due_date": "2024-01-05T23:59:59",
      "taken_at": "2024-01-01T10:30:00",
      "completed_at": null,
      "report": {
        "id": "report-uuid",
        "image_url": "https://...",
        "reporter_name": "Rahim Ahmed"
      }
    }
  ]
}
```

---

### 7. Complete Task
**POST** `/api/cleaner/tasks/<task_id>/complete`

Mark a task as completed with evidence.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Request Body:**
```json
{
  "evidence_image_url": "https://example.com/after-cleanup.jpg",
  "after_image_url": "https://example.com/final-result.jpg",
  "notes": "Area completely cleaned, all waste removed"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Task completed successfully",
  "data": {
    "id": "task-uuid",
    "status": "COMPLETED",
    "completed_at": "2024-01-02T15:45:00",
    "earnings": 500.00
  }
}
```

---

### 8. Get Task Details
**GET** `/api/cleaner/tasks/<task_id>`

Get detailed information about a specific task.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "task": {
      "id": "task-uuid",
      "description": "Clean overflowing garbage bin",
      "priority": "HIGH",
      "status": "COMPLETED",
      "reward": 500.00,
      "due_date": "2024-01-05T23:59:59",
      "taken_at": "2024-01-01T10:30:00",
      "completed_at": "2024-01-02T15:45:00",
      "evidence_image_url": "https://..."
    },
    "zone": {
      "id": "zone-uuid",
      "name": "Dhanmondi Park",
      "cleanliness_score": 85
    },
    "report": {
      "id": "report-uuid",
      "description": "Overflowing garbage bin",
      "image_url": "https://...",
      "after_image_url": "https://...",
      "reporter_name": "Rahim Ahmed"
    },
    "ai_analysis": {
      "estimated_volume": "2-3 cubic meters",
      "environmental_impact": "MODERATE",
      "recommended_action": "Immediate cleanup required",
      "special_equipment": ["Gloves", "Waste bags"]
    },
    "review": {
      "rating": 5,
      "comment": "Excellent work! Area is completely clean.",
      "created_at": "2024-01-03T09:15:00"
    }
  }
}
```

---

### 9. Get Earnings History
**GET** `/api/cleaner/earnings`

Get earnings transaction history.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Query Parameters:**
- `status` - Filter by status (PENDING, PAID)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 35,
  "total_earnings": 25000.00,
  "pending_earnings": 1500.00,
  "data": [
    {
      "id": "transaction-uuid",
      "task_id": "task-uuid",
      "amount": 500.00,
      "status": "PAID",
      "created_at": "2024-01-02T15:45:00",
      "paid_at": "2024-01-05T10:00:00",
      "task_description": "Clean overflowing garbage bin"
    }
  ]
}
```

---

### 10. Get Reviews
**GET** `/api/cleaner/reviews`

Get all reviews received from citizens.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Query Parameters:**
- `rating` - Filter by rating (1-5)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 28,
  "average_rating": 4.75,
  "data": [
    {
      "id": "review-uuid",
      "rating": 5,
      "comment": "Excellent work! The area is completely clean now.",
      "citizen_name": "Rahim Ahmed",
      "report_id": "report-uuid",
      "task_description": "Clean overflowing garbage bin",
      "created_at": "2024-01-03T09:15:00"
    }
  ]
}
```

---

### 11. Get Cleaner Leaderboard
**GET** `/api/cleaner/leaderboard`

Get cleaner leaderboard rankings.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Query Parameters:**
- `period` - Time period (all_time, month, week) - default: all_time
- `limit` - Limit results (default: 10)

**Response (200):**
```json
{
  "success": true,
  "period": "all_time",
  "my_rank": 5,
  "data": [
    {
      "rank": 1,
      "user_name": "Mohammad Hassan",
      "avatar_url": "https://...",
      "total_earnings": 45000.00,
      "completed_tasks": 120,
      "rating": 4.9,
      "this_month_earnings": 3500.00
    }
  ]
}
```

---

### 12. Get Notifications
**GET** `/api/cleaner/notifications`

Get cleaner notifications.

**Headers:**
```
Authorization: Bearer <cleaner_token>
```

**Query Parameters:**
- `is_read` - Filter by read status (true/false)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "unread_count": 2,
  "data": [
    {
      "id": "notification-uuid",
      "type": "TASK",
      "title": "New Task Available",
      "message": "A new cleanup task is available in your area. Reward: ৳500",
      "is_read": false,
      "related_task_id": "task-uuid",
      "created_at": "2024-01-01T10:30:00"
    }
  ]
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

### 6. Get Pending Reports
**GET** `/api/admin/reports/pending`

Get all reports pending approval.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `severity` - Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
- `zone_id` - Filter by zone
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 10,
  "data": [
    {
      "id": "report-uuid",
      "user_name": "Rahim Ahmed",
      "zone_name": "Dhanmondi Park",
      "description": "Overflowing garbage bin near park entrance",
      "severity": "HIGH",
      "image_url": "https://...",
      "latitude": 23.8103,
      "longitude": 90.4125,
      "created_at": "2024-01-01T10:30:00",
      "ai_analysis": {
        "description": "Mixed waste including plastic bottles",
        "estimated_volume": "2-3 cubic meters",
        "environmental_impact": "MODERATE",
        "health_hazard": true
      }
    }
  ]
}
```

---

### 7. Approve Report
**POST** `/api/admin/reports/<report_id>/approve`

Approve a report and create a cleanup task.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "reward_amount": 500.00,
  "due_date": "2024-01-05T23:59:59",
  "notes": "High priority cleanup required"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Report approved and task created",
  "data": {
    "report_id": "report-uuid",
    "task_id": "task-uuid",
    "reward_amount": 500.00,
    "points_awarded": 40
  }
}
```

---

### 8. Decline Report
**POST** `/api/admin/reports/<report_id>/decline`

Decline a report with reason.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "decline_reason": "Duplicate report - already addressed"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Report declined",
  "data": {
    "report_id": "report-uuid",
    "decline_reason": "Duplicate report - already addressed"
  }
}
```

---

### 9. Get All Reports
**GET** `/api/admin/reports`

Get all reports with filtering.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status` - Filter by status
- `severity` - Filter by severity
- `zone_id` - Filter by zone
- `user_id` - Filter by user
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 50,
  "data": [
    {
      "id": "report-uuid",
      "user_name": "Rahim Ahmed",
      "zone_name": "Dhanmondi Park",
      "description": "Overflowing garbage bin",
      "severity": "HIGH",
      "status": "COMPLETED",
      "cleaner_name": "Abdul Karim",
      "created_at": "2024-01-01T10:30:00",
      "completed_at": "2024-01-02T15:45:00"
    }
  ]
}
```

---

### 10. Get All Tasks
**GET** `/api/admin/tasks`

Get all tasks with filtering.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status` - Filter by status
- `priority` - Filter by priority
- `zone_id` - Filter by zone
- `cleaner_id` - Filter by cleaner
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 15,
  "data": [
    {
      "id": "task-uuid",
      "zone_name": "Dhanmondi Park",
      "description": "Clean overflowing garbage bin",
      "priority": "HIGH",
      "status": "IN_PROGRESS",
      "reward": 500.00,
      "cleaner_name": "Abdul Karim",
      "due_date": "2024-01-05T23:59:59",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

---

### 11. Create Manual Task
**POST** `/api/admin/tasks`

Create a manual cleanup task (not from report).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "zone_id": "zone-uuid",
  "description": "Regular maintenance cleanup of park area",
  "priority": "MEDIUM",
  "due_date": "2024-01-10T23:59:59",
  "reward": 300.00
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Task created successfully",
  "data": {
    "id": "task-uuid",
    "zone_name": "Dhanmondi Park",
    "description": "Regular maintenance cleanup of park area",
    "priority": "MEDIUM",
    "reward": 300.00,
    "status": "APPROVED"
  }
}
```

---

### 12. Get Zones
**GET** `/api/admin/zones`

Get all zones with statistics.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `is_active` - Filter by active status (true/false)
- `limit` - Limit results (default: all)

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "zone-uuid",
      "name": "Dhanmondi Park",
      "description": "Central park area in Dhanmondi",
      "cleanliness_score": 85,
      "color": "#3b82f6",
      "is_active": true,
      "total_reports": 25,
      "pending_reports": 3,
      "active_tasks": 2,
      "polygon_points": [
        {"latitude": 23.8103, "longitude": 90.4125},
        {"latitude": 23.8120, "longitude": 90.4140}
      ]
    }
  ]
}
```

---

### 13. Create Zone
**POST** `/api/admin/zones`

Create a new service zone.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "name": "New Park Area",
  "description": "Newly designated park area for waste management",
  "color": "#10b981",
  "polygon_points": [
    {"latitude": 23.8103, "longitude": 90.4125},
    {"latitude": 23.8120, "longitude": 90.4140},
    {"latitude": 23.8115, "longitude": 90.4155},
    {"latitude": 23.8098, "longitude": 90.4140}
  ]
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Zone created successfully",
  "data": {
    "id": "zone-uuid",
    "name": "New Park Area",
    "cleanliness_score": 100,
    "is_active": true
  }
}
```

---

### 14. Update Zone
**PUT** `/api/admin/zones/<zone_id>`

Update zone information.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "name": "Updated Park Area",
  "description": "Updated description",
  "color": "#ef4444",
  "is_active": false
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Zone updated successfully",
  "data": {
    "id": "zone-uuid",
    "name": "Updated Park Area",
    "is_active": false
  }
}
```

---

### 15. Get Zone Details
**GET** `/api/admin/zones/<zone_id>`

Get detailed zone information with statistics.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "zone": {
      "id": "zone-uuid",
      "name": "Dhanmondi Park",
      "description": "Central park area",
      "cleanliness_score": 85,
      "color": "#3b82f6",
      "is_active": true
    },
    "statistics": {
      "total_reports": 25,
      "pending_reports": 3,
      "completed_reports": 20,
      "active_tasks": 2,
      "avg_completion_time": "2 days 5 hours"
    },
    "polygon_points": [
      {"latitude": 23.8103, "longitude": 90.4125, "point_order": 0},
      {"latitude": 23.8120, "longitude": 90.4140, "point_order": 1}
    ]
  }
}
```

---

### 16. Process Payments
**POST** `/api/admin/payments/process`

Process pending payments for cleaners.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "transaction_ids": ["transaction-uuid-1", "transaction-uuid-2"],
  "payment_method": "bank_transfer",
  "notes": "Monthly payment batch"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Payments processed successfully",
  "data": {
    "processed_count": 2,
    "total_amount": 1500.00,
    "transaction_ids": ["transaction-uuid-1", "transaction-uuid-2"]
  }
}
```

---

### 17. Get Pending Payments
**GET** `/api/admin/payments/pending`

Get all pending payment transactions.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `cleaner_id` - Filter by cleaner
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "total": 8,
  "total_amount": 4500.00,
  "data": [
    {
      "id": "transaction-uuid",
      "cleaner_name": "Abdul Karim",
      "task_description": "Clean overflowing garbage bin",
      "amount": 500.00,
      "created_at": "2024-01-02T15:45:00",
      "task_completed_at": "2024-01-02T15:45:00"
    }
  ]
}
```

---

### 18. Send Bulk Notification
**POST** `/api/admin/notifications/bulk`

Send notification to multiple users.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "audience": "citizens",
  "type": "announcement",
  "title": "System Maintenance",
  "message": "The system will be under maintenance tomorrow from 2-4 AM."
}
```

**Audience Options:** `all`, `citizens`, `cleaners`

**Response (200):**
```json
{
  "success": true,
  "message": "Bulk notification sent successfully",
  "data": {
    "audience": "citizens",
    "recipients_count": 12,
    "sent_at": "2024-01-01T10:30:00"
  }
}
```

---

### 19. Get Alerts
**GET** `/api/admin/alerts`

Get system alerts.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status` - Filter by status (OPEN, RESOLVED)
- `severity` - Filter by severity
- `source` - Filter by source (AI, CITIZEN)
- `limit` - Limit results (default: 20)

**Response (200):**
```json
{
  "success": true,
  "total": 3,
  "data": [
    {
      "id": "alert-uuid",
      "source": "AI",
      "zone_name": "Dhanmondi Park",
      "severity": "HIGH",
      "status": "OPEN",
      "message": "Zone cleanliness has dropped below 50%",
      "created_at": "2024-01-01T10:30:00"
    }
  ]
}
```

---

### 20. Resolve Alert
**POST** `/api/admin/alerts/<alert_id>/resolve`

Mark an alert as resolved.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "resolution_notes": "Additional cleanup tasks assigned to the zone"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Alert resolved successfully",
  "data": {
    "alert_id": "alert-uuid",
    "resolved_at": "2024-01-01T15:30:00"
  }
}
```

---

### 21. Get Analytics Dashboard
**GET** `/api/admin/analytics`

Get comprehensive analytics data.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `period` - Time period (week, month, quarter, year) - default: month

**Response (200):**
```json
{
  "success": true,
  "period": "month",
  "data": {
    "reports": {
      "total": 45,
      "approved": 38,
      "declined": 3,
      "pending": 4,
      "by_severity": {
        "LOW": 15,
        "MEDIUM": 20,
        "HIGH": 8,
        "CRITICAL": 2
      }
    },
    "tasks": {
      "total": 38,
      "completed": 35,
      "in_progress": 3,
      "avg_completion_time": "1.5 days"
    },
    "users": {
      "new_citizens": 5,
      "new_cleaners": 2,
      "active_citizens": 12,
      "active_cleaners": 8
    },
    "zones": {
      "avg_cleanliness": 82.5,
      "most_reported": "Dhanmondi Park",
      "cleanest": "Gulshan Lake"
    },
    "earnings": {
      "total_paid": 18500.00,
      "pending": 2500.00,
      "avg_per_task": 486.84
    }
  }
}
```

---

## Zones & Maps Endpoints

### 1. Get All Zones
**GET** `/api/zones`

Get all active zones with basic information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "zone-uuid",
      "name": "Dhanmondi Park",
      "description": "Central park area in Dhanmondi",
      "cleanliness_score": 85,
      "color": "#3b82f6",
      "polygon_points": [
        {"latitude": 23.8103, "longitude": 90.4125, "point_order": 0},
        {"latitude": 23.8120, "longitude": 90.4140, "point_order": 1},
        {"latitude": 23.8115, "longitude": 90.4155, "point_order": 2},
        {"latitude": 23.8098, "longitude": 90.4140, "point_order": 3}
      ]
    }
  ]
}
```

---

### 2. Get Zone by Location
**GET** `/api/zones/by-location`

Find zone by coordinates.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `latitude` - Latitude coordinate (required)
- `longitude` - Longitude coordinate (required)

**Example:**
```
GET /api/zones/by-location?latitude=23.8103&longitude=90.4125
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "zone-uuid",
    "name": "Dhanmondi Park",
    "cleanliness_score": 85,
    "color": "#3b82f6"
  }
}
```

---

### 3. Get Zone Statistics
**GET** `/api/zones/<zone_id>/stats`

Get detailed statistics for a specific zone.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "zone_id": "zone-uuid",
    "zone_name": "Dhanmondi Park",
    "cleanliness_score": 85,
    "total_reports": 25,
    "pending_reports": 3,
    "completed_reports": 20,
    "active_tasks": 2,
    "avg_completion_time": "2 days 5 hours",
    "recent_reports": [
      {
        "id": "report-uuid",
        "description": "Overflowing bin",
        "severity": "MEDIUM",
        "status": "SUBMITTED",
        "created_at": "2024-01-01T10:30:00"
      }
    ]
  }
}
```

---

## AI Analysis Endpoints

### 1. Analyze Waste Image
**POST** `/api/ai/analyze-waste`

Submit image for AI waste analysis.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "image_url": "https://example.com/waste-image.jpg",
  "location": {
    "latitude": 23.8103,
    "longitude": 90.4125
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "description": "Mixed waste including plastic bottles, food waste, and paper",
    "severity": "MEDIUM",
    "estimated_volume": "2-3 cubic meters",
    "environmental_impact": "MODERATE",
    "health_hazard": true,
    "hazard_details": "Potential bacterial growth from organic waste",
    "recommended_action": "Immediate cleanup required with proper protective equipment",
    "estimated_cleanup_time": "2-3 hours",
    "confidence": 85,
    "waste_composition": [
      {"waste_type": "Plastic", "percentage": 40, "recyclable": true},
      {"waste_type": "Organic", "percentage": 35, "recyclable": false},
      {"waste_type": "Paper", "percentage": 20, "recyclable": true},
      {"waste_type": "Metal", "percentage": 5, "recyclable": true}
    ],
    "special_equipment": ["Gloves", "Masks", "Waste bags", "Broom"]
  }
}
```

---

### 2. Compare Cleanup Images
**POST** `/api/ai/compare-cleanup`

Compare before and after cleanup images.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "before_image_url": "https://example.com/before.jpg",
  "after_image_url": "https://example.com/after.jpg",
  "report_id": "report-uuid"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "completion_percentage": 95,
    "before_summary": "Large pile of mixed waste with overflowing bins",
    "after_summary": "Area completely cleaned, bins emptied and organized",
    "quality_rating": "EXCELLENT",
    "environmental_benefit": "Significant improvement in area cleanliness and hygiene",
    "verification_status": "VERIFIED",
    "feedback": "Outstanding cleanup work, area restored to excellent condition",
    "confidence": 92,
    "waste_removed": [
      {"waste_type": "Plastic", "percentage": 45, "recyclable": true},
      {"waste_type": "Organic", "percentage": 30, "recyclable": false},
      {"waste_type": "Paper", "percentage": 25, "recyclable": true}
    ],
    "remaining_issues": []
  }
}
```

---

## Notifications Endpoints

### 1. Get Notifications (All Roles)
**GET** `/api/notifications`

Get user notifications (works for all roles).

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `is_read` - Filter by read status (true/false)
- `type` - Filter by type (POINTS, BADGE, REPORT, TASK, ALERT, ANNOUNCEMENT)
- `limit` - Limit results (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response (200):**
```json
{
  "success": true,
  "unread_count": 5,
  "total": 25,
  "data": [
    {
      "id": "notification-uuid",
      "type": "REPORT",
      "title": "Report Approved!",
      "message": "Your waste report has been approved! You earned 25 bonus points.",
      "is_read": false,
      "related_report_id": "report-uuid",
      "related_task_id": null,
      "created_at": "2024-01-01T10:30:00"
    }
  ]
}
```

---

### 2. Mark Notification as Read
**PUT** `/api/notifications/<notification_id>/read`

Mark a specific notification as read.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

---

### 3. Mark All Notifications as Read
**PUT** `/api/notifications/read-all`

Mark all user notifications as read.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "All notifications marked as read",
  "count": 5
}
```

---

## Leaderboards Endpoints

### 1. Get Citizen Leaderboard
**GET** `/api/leaderboards/citizens`

Get citizen leaderboard rankings.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `period` - Time period (all_time, month, week) - default: all_time
- `limit` - Limit results (default: 10)

**Response (200):**
```json
{
  "success": true,
  "period": "all_time",
  "data": [
    {
      "rank": 1,
      "user_id": "user-uuid",
      "user_name": "Fatima Khan",
      "avatar_url": "https://...",
      "total_green_points": 1250,
      "approved_reports": 45,
      "badges_count": 6
    }
  ]
}
```

---

### 2. Get Cleaner Leaderboard
**GET** `/api/leaderboards/cleaners`

Get cleaner leaderboard rankings.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `period` - Time period (all_time, month, week) - default: all_time
- `limit` - Limit results (default: 10)

**Response (200):**
```json
{
  "success": true,
  "period": "all_time",
  "data": [
    {
      "rank": 1,
      "user_id": "user-uuid",
      "user_name": "Mohammad Hassan",
      "avatar_url": "https://...",
      "total_earnings": 45000.00,
      "completed_tasks": 120,
      "rating": 4.9,
      "this_month_earnings": 3500.00
    }
  ]
}
```

---

## Reports Endpoints (General)

### 1. Get Report Details (Any Role)
**GET** `/api/reports/<report_id>`

Get detailed report information (accessible by report owner, assigned cleaner, or admin).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "report": {
      "id": "report-uuid",
      "description": "Overflowing garbage bin near park entrance",
      "severity": "MEDIUM",
      "status": "COMPLETED",
      "image_url": "https://...",
      "after_image_url": "https://...",
      "latitude": 23.8103,
      "longitude": 90.4125,
      "created_at": "2024-01-01T10:30:00",
      "completed_at": "2024-01-02T15:45:00"
    },
    "reporter": {
      "id": "user-uuid",
      "name": "Rahim Ahmed",
      "avatar_url": "https://..."
    },
    "zone": {
      "id": "zone-uuid",
      "name": "Dhanmondi Park",
      "cleanliness_score": 85
    },
    "cleaner": {
      "id": "cleaner-uuid",
      "name": "Abdul Karim",
      "rating": 4.5,
      "avatar_url": "https://..."
    },
    "task": {
      "id": "task-uuid",
      "reward": 500.00,
      "due_date": "2024-01-05T23:59:59",
      "taken_at": "2024-01-01T12:00:00",
      "completed_at": "2024-01-02T15:45:00"
    },
    "ai_analysis": {
      "description": "Mixed waste including plastic bottles and food waste",
      "estimated_volume": "2-3 cubic meters",
      "environmental_impact": "MODERATE",
      "health_hazard": true,
      "recommended_action": "Immediate cleanup required",
      "waste_composition": [
        {"waste_type": "Plastic", "percentage": 40, "recyclable": true}
      ]
    },
    "cleanup_comparison": {
      "completion_percentage": 95,
      "quality_rating": "EXCELLENT",
      "environmental_benefit": "Significant improvement in area cleanliness"
    },
    "review": {
      "rating": 5,
      "comment": "Excellent work! The area is completely clean now.",
      "created_at": "2024-01-03T09:15:00"
    }
  }
}
```

---

## Tasks Endpoints (General)

### 1. Get Task Details (Any Role)
**GET** `/api/tasks/<task_id>`

Get detailed task information (accessible by task owner or admin).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "task": {
      "id": "task-uuid",
      "description": "Clean overflowing garbage bin near park entrance",
      "priority": "HIGH",
      "status": "COMPLETED",
      "reward": 500.00,
      "due_date": "2024-01-05T23:59:59",
      "created_at": "2024-01-01T12:00:00",
      "taken_at": "2024-01-01T14:30:00",
      "completed_at": "2024-01-02T15:45:00",
      "evidence_image_url": "https://..."
    },
    "zone": {
      "id": "zone-uuid",
      "name": "Dhanmondi Park",
      "cleanliness_score": 85
    },
    "cleaner": {
      "id": "cleaner-uuid",
      "name": "Abdul Karim",
      "rating": 4.5,
      "avatar_url": "https://..."
    },
    "report": {
      "id": "report-uuid",
      "description": "Overflowing garbage bin",
      "image_url": "https://...",
      "after_image_url": "https://...",
      "reporter_name": "Rahim Ahmed"
    },
    "earnings": {
      "transaction_id": "transaction-uuid",
      "amount": 500.00,
      "status": "PAID",
      "paid_at": "2024-01-05T10:00:00"
    }
  }
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

### 422 Validation Error
```json
{
  "success": false,
  "error": "Validation failed",
  "details": {
    "severity": "Invalid severity level. Must be one of: LOW, MEDIUM, HIGH, CRITICAL",
    "latitude": "Latitude must be between -90 and 90"
  }
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal server error"
}
```

---

## API Endpoint Summary

### Authentication (4 endpoints)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user

### Citizen (13 endpoints)
- `GET /api/citizen/profile` - Get profile
- `PUT /api/citizen/profile` - Update profile
- `GET /api/citizen/stats` - Get statistics
- `POST /api/citizen/reports` - Submit report
- `GET /api/citizen/reports` - Get my reports
- `GET /api/citizen/reports/<id>` - Get report details
- `POST /api/citizen/reports/<id>/review` - Submit cleanup review
- `GET /api/citizen/badges` - Get my badges
- `GET /api/citizen/points` - Get points history
- `GET /api/citizen/leaderboard` - Get leaderboard
- `GET /api/citizen/notifications` - Get notifications
- `PUT /api/citizen/notifications/<id>/read` - Mark notification read
- `PUT /api/citizen/notifications/read-all` - Mark all notifications read

### Cleaner (12 endpoints)
- `GET /api/cleaner/profile` - Get profile
- `PUT /api/cleaner/profile` - Update profile
- `GET /api/cleaner/stats` - Get statistics
- `GET /api/cleaner/tasks/available` - Get available tasks
- `POST /api/cleaner/tasks/<id>/take` - Take task
- `GET /api/cleaner/tasks` - Get my tasks
- `POST /api/cleaner/tasks/<id>/complete` - Complete task
- `GET /api/cleaner/tasks/<id>` - Get task details
- `GET /api/cleaner/earnings` - Get earnings history
- `GET /api/cleaner/reviews` - Get reviews
- `GET /api/cleaner/leaderboard` - Get leaderboard
- `GET /api/cleaner/notifications` - Get notifications

### Admin (21 endpoints)
- `GET /api/admin/profile` - Get profile
- `PUT /api/admin/profile` - Update profile
- `GET /api/admin/users` - Get all users
- `GET /api/admin/users/<id>` - Get user details
- `GET /api/admin/stats` - Get system stats
- `GET /api/admin/reports/pending` - Get pending reports
- `POST /api/admin/reports/<id>/approve` - Approve report
- `POST /api/admin/reports/<id>/decline` - Decline report
- `GET /api/admin/reports` - Get all reports
- `GET /api/admin/tasks` - Get all tasks
- `POST /api/admin/tasks` - Create manual task
- `GET /api/admin/zones` - Get zones
- `POST /api/admin/zones` - Create zone
- `PUT /api/admin/zones/<id>` - Update zone
- `GET /api/admin/zones/<id>` - Get zone details
- `POST /api/admin/payments/process` - Process payments
- `GET /api/admin/payments/pending` - Get pending payments
- `POST /api/admin/notifications/bulk` - Send bulk notification
- `GET /api/admin/alerts` - Get alerts
- `POST /api/admin/alerts/<id>/resolve` - Resolve alert
- `GET /api/admin/analytics` - Get analytics dashboard

### Zones & Maps (3 endpoints)
- `GET /api/zones` - Get all zones
- `GET /api/zones/by-location` - Find zone by coordinates
- `GET /api/zones/<id>/stats` - Get zone statistics

### AI Analysis (2 endpoints)
- `POST /api/ai/analyze-waste` - Analyze waste image
- `POST /api/ai/compare-cleanup` - Compare cleanup images

### Notifications (3 endpoints)
- `GET /api/notifications` - Get notifications (all roles)
- `PUT /api/notifications/<id>/read` - Mark notification read
- `PUT /api/notifications/read-all` - Mark all notifications read

### Leaderboards (2 endpoints)
- `GET /api/leaderboards/citizens` - Get citizen leaderboard
- `GET /api/leaderboards/cleaners` - Get cleaner leaderboard

### Reports & Tasks (2 endpoints)
- `GET /api/reports/<id>` - Get report details (any role)
- `GET /api/tasks/<id>` - Get task details (any role)

### Health (1 endpoint)
- `GET /api/health` - Check API health

**Total: 63 API Endpoints**

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

### Submit Report
```bash
curl -X POST http://127.0.0.1:5000/api/citizen/reports \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "zone-uuid",
    "description": "Overflowing garbage bin",
    "image_url": "https://example.com/image.jpg",
    "severity": "MEDIUM",
    "latitude": 23.8103,
    "longitude": 90.4125
  }'
```

### Take Task (Cleaner)
```bash
curl -X POST http://127.0.0.1:5000/api/cleaner/tasks/task-uuid/take \
  -H "Authorization: Bearer CLEANER_TOKEN_HERE"
```

### Approve Report (Admin)
```bash
curl -X POST http://127.0.0.1:5000/api/admin/reports/report-uuid/approve \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "reward_amount": 500.00,
    "due_date": "2024-12-31T23:59:59"
  }'
```

---

## Testing with Postman

### Setup Collection
1. **Import Collection**: Create a new collection "Zero Waste API"
2. **Set Base URL**: Create environment variable `base_url = http://127.0.0.1:5000`
3. **Login**: POST to `/api/auth/login` and save token to environment
4. **Set Token**: Add to collection authorization: Bearer Token `{{token}}`
5. **Test Endpoints**: Use saved token for all protected routes

### Environment Variables
```json
{
  "base_url": "http://127.0.0.1:5000",
  "token": "your_jwt_token_here",
  "citizen_token": "citizen_jwt_token",
  "cleaner_token": "cleaner_jwt_token",
  "admin_token": "admin_jwt_token"
}
```

### Pre-request Scripts
```javascript
// Auto-refresh token if expired
if (pm.environment.get("token")) {
  const token = pm.environment.get("token");
  const payload = JSON.parse(atob(token.split('.')[1]));
  const now = Math.floor(Date.now() / 1000);
  
  if (payload.exp < now) {
    console.log("Token expired, please login again");
  }
}
```

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

## Rate Limiting

### Default Limits
- **Authentication endpoints**: 5 requests per minute per IP
- **Report submission**: 10 requests per hour per user
- **General endpoints**: 100 requests per minute per user
- **Admin endpoints**: 200 requests per minute per user

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded Response
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Pagination

### Query Parameters
- `limit` - Number of items per page (default: 20, max: 100)
- `offset` - Number of items to skip (default: 0)

### Response Format
```json
{
  "success": true,
  "total": 150,
  "count": 20,
  "limit": 20,
  "offset": 0,
  "has_more": true,
  "data": [...]
}
```

---

## Filtering & Sorting

### Common Filters
- `status` - Filter by status
- `created_at_from` - Filter by creation date (ISO 8601)
- `created_at_to` - Filter by creation date (ISO 8601)
- `user_id` - Filter by user
- `zone_id` - Filter by zone

### Sorting
- `sort_by` - Field to sort by (default: created_at)
- `sort_order` - Sort order (asc/desc, default: desc)

### Example
```
GET /api/admin/reports?status=PENDING&sort_by=severity&sort_order=desc&limit=10
```

---

## WebSocket Events (Future Enhancement)

### Real-time Notifications
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://127.0.0.1:5000/ws');

// Listen for events
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Event types
{
  "type": "REPORT_APPROVED",
  "data": {
    "report_id": "uuid",
    "points_earned": 25
  }
}
```

---

**Happy Testing!** 🚀

**Total API Endpoints: 63**
**Database Tables: 25**
**Supported Roles: 3 (Citizen, Cleaner, Admin)**
**Real-time Features: Notifications, Leaderboards, Zone Updates**
