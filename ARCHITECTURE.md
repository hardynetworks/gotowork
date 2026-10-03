# 🏗️ System Architecture

## Overview

Crew Scheduler is a **FastAPI-based web application** containerized with **Docker Compose**, featuring **rule-based scheduling algorithms** for intelligent crew management.

```
┌─────────────────────────────────────────────────────────────┐
│                     Crew Scheduler App                       │
│                    (FastAPI + SQLAlchemy)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │   Frontend       │    │   Backend API    │              │
│  │ (HTMX + Alpine)  │◄──►│  (FastAPI)       │              │
│  └──────────────────┘    └────────┬─────────┘              │
│                                   │                          │
│                           ┌───────────────┐                 │
│                           │ Scheduling    │                 │
│                           │ Engine        │                 │
│                           │ (Rule-Based)  │                 │
│                           └───────┬───────┘                 │
│                                   │                          │
└───────────────────────────────────┼─────────────────────────┘
                                    │
                    ┌────────────────┼────────────────┐
                    │                │                │
        ┌───────────▼────────┐ ┌────▼──────┐ ┌──────▼──────┐
        │ PostgreSQL DB      │ │  Redis    │ │   Uvicorn   │
        │ (Data Persistence) │ │(Cache/Job)| │  Server     │
        └────────────────────┘ └────────────┘ └────────────┘
```

## Components Breakdown

### 1. **Frontend Layer** (Client-Side)

```
templates/
├── base.html          # Master layout with sidebar navigation
├── index.html         # Login/authentication page  
├── dashboard.html     # Main dashboard with stats & overview
│   ├── managers/
│   │   ├── index.html  # Crew member management
│   │   └── schedules.html # Schedule listing & creation
│   └── admin/
│       └── index.html  # Admin configuration panel
```

**Tech Stack:**
- **HTMX** - Server-driven interactions without SPA framework
- **Alpine.js** - Lightweight state management
- **Tailwind CSS** - Utility-first styling (via CDN)
- **Chart.js** - Data visualization (ready for analytics)

### 2. **Backend API Layer** (FastAPI)

```
app/
├── api/
│   ├── auth.py        # JWT authentication & role checks
│   ├── managers.py    # CRUD operations + schedule generation
│   └── admin.py       # System configuration & settings
│
├── core/
│   ├── config.py      # Application settings & defaults
│   └── scheduler.py   # Rule-based scheduling engine
│
├── models/
│   └── init.py        # SQLAlchemy database models
│       ├── Role       # User roles (admin, manager)
│       ├── User       # System users
│       ├── CrewMember # Team members to schedule
│       ├── ShiftType  # Morning/evening/night patterns
│       ├── Shift      # Individual shift records
│       ├── Schedule   # Complete schedule periods
│       ├── Constraint # Business rules & limits
│       └── SchedulingLog # Audit trail
│
├── utils/
│   └── helpers.py     # Helper functions (time, validation)
│
└── main.py            # FastAPI app initialization
```

**Key APIs:**
- `/auth/login` - User authentication
- `/managers/*` - Crew & schedule management  
- `/admin/*` - System configuration
- `/health` - Health check endpoint

### 3. **Scheduling Engine** (Rule-Based)

```python
┌─────────────────────────────────────────────────────┐
│              SCHEDULING ENGINE                       │
│                                                      │
│  Input:                                             │
│    • Period Start/End Dates                         │
│    • Location Filter                                │
│    • Available Crew Pool                            │
│                                                      │
│  Process:                                           │
│    1. Load Active Constraints                       │
│    2. Query All Shifts in Period                    │
│    3. Filter Available Crew Members                 │
│    4. Assign Shifts with Constraint Checking        │
│       ├─ Check Weekly Hours Limit                   │
│       ├─ Check Consecutive Days Limit               │
│       ├─ Verify Max Shifts Per Day                  │
│       └─ Apply Skill Matching (optional)            │
│    5. Validate Schedule Against All Rules           │
│    6. Create Scheduling Log                         │
│                                                      │
│  Output:                                            │
│    • Complete Schedule Object                       │
│    • List of Assignments                            │
│    • Constraint Violations (if any)                 │
└─────────────────────────────────────────────────────┘
```

**Constraints:**
- `max_weekly_hours` - Prevent burnout (default: 40h/week)
- `min_break_minutes` - Required rest between shifts (30m)
- `max_consecutive_days` - Mandate rest days (5 days max)

### 4. **Database Layer** (PostgreSQL)

```sql
Main Tables:
├── roles             # Admin, Manager permissions
├── users             # System user accounts
├── crew_members      # Team member data
├── shift_types       # Shift patterns (M/E/N)
├── shifts            # Individual shifts with locations
├── schedules         # Schedule periods
├── schedule_assignments  # Crew→Shift mappings
├── constraints       # Business rules config
└── scheduling_logs   # Audit trail

Views for Reporting:
├── view_crew_workload    # Workload per crew member
└── view_shift_coverage   # Coverage by location/time
```

### 5. **Infrastructure** (Docker Compose)

```yaml
Services:
┌─────────────────────────────────────┐
│         docker-compose.yml          │
├─────────────────────────────────────┤
│                                     │
│   app:                              │
│   ├── Containerized Python App      │
│   ├── Multi-stage build             │
│   ├── Health checks                 │
│   └── Hot reload (dev mode)         │
│                                     │
│   postgres:                         │
│   ├── PostgreSQL 15 (Alpine)        │
│   ├── Init scripts on startup       │
│   └── Persistent volumes            │
│                                     │
│   redis:                            │
│   ├── Redis 7 (Alpine)              │
│   ├── Cache & sessions              │
│   └── Data persistence              │
│                                     │
│   init-db:                          │
│   └── Automated schema setup        │
│                                     │
├─────────────────────────────────────┤
│  Networks: crew-network (bridge)    │
│  Volumes: postgres_data, redis_data │
└─────────────────────────────────────┘
```

## Data Flow

### Schedule Generation Flow
```
User Action → /managers/schedules POST
              │
              ▼
    ┌────────────────────┐
    │ Parse Request Data │
    │ (period, location)  │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ SchedulingEngine   │
    │ .generate_schedule()│
    └────────┬───────────┘
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
┌────────────┐  ┌────────────┐
│ Query DB   │  │ Filter Crew│
│ Shifts     │  │ Available  │
└─────┬──────┘  └─────┬──────┘
      │               │
      └─────┬─────────┘
            │
            ▼
    ┌────────────────────┐
    │ Apply Assignment   │
    │ Algorithm with     │
    │ Constraint Checks  │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Validate & Log     │
    │ Schedule Created   │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Return Response    │
    │ + Toast Notification│
    └────────────────────┘
```

## Security Considerations

1. **Authentication** - JWT tokens with short expiry (30 min)
2. **Authorization** - Role-based access control (admin/manager)
3. **Input Validation** - Pydantic models for all API requests
4. **SQL Injection** - SQLAlchemy ORM prevents injection attacks
5. **Secrets Management** - Environment variables for sensitive data
6. **Container Security** - Non-root user in production Dockerfile

## Performance Optimizations

1. **Database Indexes** - On dates, IDs, and status fields
2. **Connection Pooling** - SQLAlchemy async pool (size: 5)
3. **Cache Layer** - Redis for schedule data caching (ready to implement)
4. **HTMX Transitions** - Fast partial page updates
5. **Multi-stage Docker** - Minimal production image size

## Scalability Considerations

- **Horizontal Scaling**: Stateless app containers can be replicated
- **Database**: PostgreSQL supports read replicas
- **Queue**: Ready for Celery/RQ integration (Redis available)
- **CDN**: Static files ready for CDN distribution

---

This architecture provides a solid foundation for crew scheduling that's production-ready, secure, and easy to extend! 🚀