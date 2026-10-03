# 📅 Crew Scheduler

A modern web-based crew scheduling application built with **FastAPI**, **Docker Compose**, and **rule-based scheduling algorithms**. Perfect for managing team schedules across multiple locations with built-in constraints and automation.

![Crew Scheduler](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-D24354?logo=docker&logoColor=white) ![Python](https://img.shields.io/badge/Python-3.11-blue.svg)

## ✨ Features

### 🎯 Core Functionality
- **Rule-Based Scheduling Engine**: Automatic schedule generation with intelligent constraint handling
- **Crew Member Management**: Add, edit, and manage team members with skill levels
- **Shift Type Configuration**: Morning, Evening, Night shifts with customizable timing
- **Multi-Location Support**: Schedule crews across multiple locations
- **Schedule Generation**: One-click schedule creation based on business rules

### 🔒 Role-Based Access Control
- **Admin Panel**: System configuration, constraint management, audit logs
- **Manager Dashboard**: Crew management and schedule viewing
- **User Authentication**: Secure login with JWT tokens
- **Role Separation**: Different access levels for different user types

### ⚙️ Business Rules & Constraints
- **Maximum Weekly Hours**: Prevent crew from overworking (default: 40h/week)
- **Consecutive Days Limit**: Rest requirements between shifts (default: 5 days max)
- **Shift Coverage**: Ensure adequate staffing levels
- **Break Management**: Minimum break enforcement between shifts

### 📊 Monitoring & Analytics
- **Dashboard Overview**: Real-time statistics on crew, shifts, and schedules
- **Activity Logs**: Complete audit trail of all scheduling actions
- **Workload Reports**: Identify overworked team members
- **Coverage Metrics**: Track shift coverage by location and time

### 🐳 Docker Deployment
- **Production-Ready**: Multi-stage Docker build with PostgreSQL & Redis
- **Auto-Recovery**: Automatic container restart on failures
- **Health Checks**: Built-in monitoring for all services
- **Volume Persistence**: Data persistence across container restarts

## 🚀 Quick Start

### Prerequisites
- [Docker](https://docker.com) (latest version)
- [Git](https://git-scm.com) (optional, for cloning)

### Installation

1. **Clone or navigate to the project directory:**
```bash
cd crew-scheduler
```

2. **Start all services with Docker Compose:**
```bash
docker-compose up -d
```

This will automatically:
- Build and start the main application container
- Initialize PostgreSQL database
- Set up Redis cache
- Create default roles (admin, manager)

3. **Access the application:**
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

### Default Login Credentials

```
Email: admin@crew-scheduler.com
Password: admin123
```

## 📁 Project Structure

```
crew-scheduler/
├── app/                          # Application code
│   ├── api/                      # API endpoints
│   │   ├── auth.py              # Authentication routes
│   │   ├── managers.py          # Manager CRUD & scheduling
│   │   └── admin.py             # Admin configuration
│   ├── core/                     # Core logic
│   │   ├── config.py            # Application settings
│   │   └── scheduler.py         # Rule-based scheduling engine
│   ├── models/                   # SQLAlchemy database models
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html            # Main layout with sidebar
│   │   ├── index.html           # Login page
│   │   ├── dashboard.html       # Home dashboard
│   │   ├── managers/index.html  # Crew management
│   │   └── managers/schedules.html # Schedule view
│   ├── utils/                    # Helper utilities
│   ├── static/                   # CSS, JS, images
│   └── main.py                   # FastAPI application entry
├── docker-compose.yml            # Service orchestration
├── Dockerfile                    # Application container definition
├── init.sql                      # PostgreSQL initialization script
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
└── README.md                     # This file
```

## 🔧 Configuration

### Scheduling Rules (Admin Panel)

Configure scheduling constraints via the Admin panel:

- **Max Weekly Hours**: Maximum hours per crew member per week (default: 40)
- **Min Break Minutes**: Required break between shifts (default: 30 minutes)
- **Max Consecutive Days**: Work days before mandatory rest (default: 5)

### Environment Variables

Edit `.env` file for customization:

```bash
DATABASE_URL="postgresql://admin:password123@postgres:5432/crew_scheduler"
REDIS_URL="redis://redis:6379/0"
SECRET_KEY="your-secret-key-here"
DEBUG=true
```

## 🎨 UI Screenshots

### Dashboard
- Real-time statistics (active crew, shifts, assignments)
- Quick actions for common tasks
- Weekly schedule overview
- Recent activity feed

### Crew Management
- Full CRUD operations via HTMX
- Pagination and search
- Skill level filtering
- Status indicators

### Schedules
- Grid view of all schedules
- Filter by status (draft/active)
- Quick generate button
- Coverage statistics

### Admin Panel
- Constraint configuration with live updates
- System information display
- Audit log with pagination
- Quick system initialization

## 🛠️ Development

### Local Development Mode

To run without Docker for local development:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Schema

The application uses PostgreSQL with the following main tables:

- `roles` - System roles (admin, manager)
- `users` - User accounts
- `crew_members` - Team member data
- `shift_types` - Shift patterns (morning/evening/night)
- `shifts` - Individual shift records
- `schedules` - Complete schedule periods
- `schedule_assignments` - Crew-to-shift assignments
- `constraints` - Business rules and limits
- `scheduling_logs` - Audit trail

## 📈 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Managers
- `GET /managers/crew-members` - List crew members
- `POST /managers/crew-members` - Create crew member
- `POST /managers/schedules` - Generate new schedule
- `GET /managers/schedules` - List schedules

### Admin
- `GET /admin/settings` - Get current settings
- `POST /admin/settings/quick-update` - Update constraints
- `GET /admin/audit/logs` - View audit logs
- `POST /admin/init` - Initialize system

See API docs at: http://localhost:8000/docs

## 🔄 Scheduling Algorithm

The rule-based scheduler works as follows:

1. **Analyze Available Crew**: Filter by employment period and active status
2. **Find Shifts in Period**: Query shifts within the requested date range
3. **Apply Constraints**: Check against weekly hours, consecutive days, etc.
4. **Assign Fairly**: Round-robin assignment for balance
5. **Validate Results**: Ensure all constraints are met
6. **Log Operations**: Record scheduling decisions

### Constraint Enforcement

```python
# Example constraint checking logic
def check_constraints(assignment, crew_member):
    # Weekly hours limit
    weekly_hours = calculate_weekly_hours(crew_member)
    if weekly_hours > MAX_WEEKLY_HOURS:
        raise Violation("Exceeds weekly hour limit")
    
    # Consecutive days
    consecutive_count = count_consecutive_days(crew_member)
    if consecutive_count >= MAX_CONSECUTIVE_DAYS:
        raise Violation("Too many consecutive work days")
```

## 🐛 Troubleshooting

### Container won't start
```bash
# Check Docker logs
docker-compose logs app

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database connection issues
```bash
# Ensure PostgreSQL is running
docker-compose ps postgres

# Test database connectivity
docker exec crew-scheduler-postgres pg_isready -U admin -d crew_scheduler
```

### Reset everything
```bash
# Delete all volumes and containers
docker-compose down -v
docker-compose up -d
```

## 📝 Roadmap

- [ ] Shift swap functionality
- [ ] Bulk schedule updates
- [ ] Email notifications for staff
- [ ] Mobile-responsive improvements
- [ ] Advanced analytics dashboard
- [ ] Export to CSV/PDF
- [ ] REST API authentication (OAuth2)
- [ ] Background job processing (Celery/RQ)

## 🤝 Contributing

Contributions welcome! Feel free to submit issues and pull requests.

## 📄 License

This project is open source and available under the MIT License.

## 👥 Credits

Built with ❤️ using:
- FastAPI + SQLAlchemy
- PostgreSQL + Redis
- Docker Compose
- HTMX for dynamic interactions
- Tailwind CSS for styling

---

**Happy Scheduling! 📅✨**