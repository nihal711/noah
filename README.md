# Noah HR Management API

A comprehensive HR Management REST API built with FastAPI and PostgreSQL, featuring Swagger documentation for all endpoints.

## Features

### 🔐 Authentication
- JWT token-based authentication
- Login/logout functionality
- Secure password hashing

### 👥 User Management
- Create and manage user accounts
- Employee information management
- Role-based access control

### 🏖️ Leave Management
- Apply for leave requests
- View leave status and history
- Check leave balances
- Manager approval workflow

### 🏦 Bank Letter Requests
- Request official bank letters
- Track request status
- HR approval workflow

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd noah-hr-api
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Database Setup**
Make sure your PostgreSQL server is running and create the `noah` database:
```sql
CREATE DATABASE noah;
```

4. **Environment Configuration**
Update the database URL in `config.py` if needed:
```python
DATABASE_URL = "postgresql://postgres:JCc66c7TKIP8q7@127.0.0.1:5433/noah"
```

5. **Initialize Database**
```bash
python init_db.py
```

6. **Run the Application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8181
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8181/docs
- **ReDoc**: http://localhost:8181/redoc

## Sample Users

The initialization script creates the following demo users:

| Username | Password | Department | Position |
|----------|----------|------------|----------|
| john_doe | password123 | Engineering | Software Developer |
| jane_smith | password123 | Human Resources | HR Manager |
| mike_johnson | password123 | Engineering | Team Lead |
| sarah_wilson | password123 | Marketing | Marketing Specialist |

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user info

### User Management
- `POST /users/` - Create new user
- `GET /users/` - Get all users
- `GET /users/{user_id}` - Get user by ID
- `DELETE /users/{user_id}` - Delete user

### Leave Management
- `POST /leave/requests` - Apply for leave
- `GET /leave/requests` - Get my leave requests
- `GET /leave/requests/all` - Get all leave requests (manager)
- `GET /leave/requests/{request_id}` - Get specific leave request
- `PUT /leave/requests/{request_id}` - Update leave request status
- `DELETE /leave/requests/{request_id}` - Delete leave request
- `GET /leave/balance` - Get my leave balance
- `GET /leave/balance/{user_id}` - Get user's leave balance

### Bank Letter Requests
- `POST /bank-letter/` - Request bank letter
- `GET /bank-letter/` - Get my bank letter requests
- `GET /bank-letter/all` - Get all bank letter requests (HR)
- `GET /bank-letter/{request_id}` - Get specific bank letter request
- `PUT /bank-letter/{request_id}` - Update bank letter request status
- `DELETE /bank-letter/{request_id}` - Delete bank letter request

## Example Usage

### 1. Login
```bash
curl -X POST "http://localhost:8181/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=password123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Apply for Leave
```bash
curl -X POST "http://localhost:8181/leave/requests" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "leave_type": "Annual",
    "start_date": "2024-12-25T00:00:00",
    "end_date": "2024-12-27T00:00:00",
    "days_requested": 3.0,
    "reason": "Christmas vacation"
  }'
```

### 3. Request Bank Letter
```bash
curl -X POST "http://localhost:8181/bank-letter/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bank_name": "ABC Bank",
    "purpose": "Home loan application",
    "additional_details": "Need employment verification letter"
  }'
```

## Database Schema

The API uses the following main tables:
- `users` - Employee information and authentication
- `leave_requests` - Leave applications and status
- `leave_balances` - Annual leave entitlements
- `bank_letter_requests` - Bank letter requests and status

## Security Features

- Password hashing using bcrypt
- JWT token authentication
- User session management
- Input validation and sanitization
- SQL injection prevention through ORM

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Production Deployment

1. Set environment variables for production
2. Configure CORS settings appropriately
3. Use a production WSGI server like Gunicorn
4. Set up proper database connection pooling
5. Implement proper logging and monitoring

## Support

For questions or issues, please check the API documentation at `/docs` or contact the development team.

## License

This project is licensed under the MIT License.