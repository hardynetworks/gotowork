# 🚀 Quick Start Guide

Get your Crew Scheduler running in under 5 minutes!

## Option 1: Docker (Recommended) ⭐

### 1. Start all services
```bash
docker-compose up -d
```

### 2. Open the application
- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Login with default credentials
```
Email: admin@crew-scheduler.com
Password: admin123
```

That's it! The app will automatically:
- Build the Python application container
- Start PostgreSQL database
- Configure Redis cache
- Create default admin user

---

## Option 2: Local Development (Windows/Mac/Linux)

### Windows

```cmd
cd crew-scheduler
run_local.bat
```

### Mac/Linux

```bash
cd crew-scheduler
chmod +x run_local.sh
./run_local.sh
```

---

## What You'll Get

### 📊 Dashboard Features
- Overview of all crew members (47 active)
- Schedule assignments statistics
- Quick actions for common tasks
- Weekly schedule preview

### 👥 Crew Management
- Add/Edit/Delete crew members
- Skill level tracking
- Employment date management
- Active/inactive status

### 📅 Scheduling
- Generate schedules automatically
- Rule-based assignment (no overwork)
- Multi-location support
- Status tracking (draft/active)

### ⚙️ Admin Tools
- Configure scheduling constraints
- View system statistics
- Audit logs for tracking changes
- Quick system initialization

---

## Default Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Max Weekly Hours | 40h | Can't work more per week |
| Min Break | 30min | Required break between shifts |
| Consecutive Days | 5 | Max work days in a row |

---

## Next Steps After Login

1. **Add Crew Members**: Go to Managers page and add your team
2. **Configure Constraints**: Adjust rules in Admin panel
3. **Generate Schedule**: Create your first schedule period
4. **View Analytics**: Check the dashboard for insights

---

## Troubleshooting

### Docker won't start
```bash
# Check logs
docker-compose logs app

# Restart everything
docker-compose down && docker-compose up -d
```

### Can't connect to database
```bash
# Verify PostgreSQL is running
docker exec crew-scheduler-postgres pg_isready -U admin -d crew_scheduler
```

### Need to reset everything
```bash
# Remove all data and restart
docker-compose down -v && docker-compose up -d
```

---

## Need Help?

- **Full Documentation**: [README.md](./README.md)
- **API Reference**: http://localhost:8000/docs
- **Project Structure**: Check the main README for details

Enjoy scheduling! 🎉