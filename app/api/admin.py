"""Admin API endpoints for system configuration."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Role, Constraint, SchedulingLog, User


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": __import__('datetime').datetime.now().isoformat()}


# ==================== ROLES ====================

@router.get("/roles/", response_model=List[Role])
async def list_roles(db: Session = Depends(get_db)):
    """List all system roles."""
    return db.query(Role).all()


@router.post("/roles/", response_model=Role)
async def create_role(role_data: Role, db: Session = Depends(get_db)):
    """Create a new role (careful with permissions!)."""
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists"
        )
    
    db.add(role_data)
    db.commit()
    db.refresh(role_data)
    return role_data


# ==================== CONSTRAINTS ====================

@router.get("/constraints/", response_model=List[Constraint])
async def list_constraints(db: Session = Depends(get_db)):
    """List all active scheduling constraints."""
    return db.query(Constraint).filter(Constraint.enabled == True).all()


@router.post("/constraints/", response_model=Constraint)
async def create_constraint(constraint: Constraint, db: Session = Depends(get_db)):
    """Create a new scheduling constraint."""
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return constraint


@router.put("/constraints/{constraint_id}", response_model=Constraint)
async def update_constraint(
    constraint_id: int,
    constraint_data: dict,
    db: Session = Depends(get_db)
):
    """Update an existing constraint."""
    constraint = db.query(Constraint).filter(Constraint.id == constraint_id).first()
    
    if not constraint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Constraint not found")
    
    for field, value in constraint_data.items():
        if hasattr(constraint, field):
            setattr(constraint, field, value)
    
    db.commit()
    db.refresh(constraint)
    
    log_entry = SchedulingLog(
        action="constraint_updated",
        details=f"Constraint '{constraint.name}' updated"
    )
    db.add(log_entry)
    
    return constraint


@router.delete("/constraints/{constraint_id}")
async def delete_constraint(
    constraint_id: int,
    db: Session = Depends(get_db)
):
    """Delete a scheduling constraint."""
    constraint = db.query(Constraint).filter(Constraint.id == constraint_id).first()
    
    if not constraint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Constraint not found")
    
    db.delete(constraint)
    db.commit()
    
    return {"message": "Constraint deleted successfully"}


# ==================== SCHEDULE SETTINGS ====================

@router.get("/settings/", response_model=dict)
async def get_schedule_settings(db: Session = Depends(get_db)):
    """Get current schedule settings from constraints."""
    constraints = db.query(Constraint).all()
    
    return {
        "max_weekly_hours": next((c.value for c in constraints if c.name == "max_weekly_hours"), 40),
        "min_break_minutes": next((c.value for c in constraints if c.name == "min_break_minutes"), 30),
        "max_consecutive_days": next((c.value for c in constraints if c.name == "max_consecutive_days"), 5)
    }


@router.post("/settings/quick-update", response_model=dict)
async def update_settings_quick(
    settings_data: dict,
    db: Session = Depends(get_db)
):
    """Quick update common schedule settings."""
    constraints = {
        "max_weekly_hours": Constraint(name="max_weekly_hours", description="Maximum weekly hours per crew member", value=settings_data.get("max_weekly_hours", 40), enabled=True),
        "min_break_minutes": Constraint(name="min_break_minutes", description="Minimum break in minutes", value=settings_data.get("min_break_minutes", 30), enabled=True),
        "max_consecutive_days": Constraint(name="max_consecutive_days", description="Maximum consecutive work days", value=settings_data.get("max_consecutive_days", 5), enabled=True)
    }
    
    for constraint in constraints.values():
        existing = db.query(Constraint).filter(Constraint.name == constraint.name).first()
        if existing:
            existing.value = constraint.value
        else:
            db.add(constraint)
    
    db.commit()
    
    return {"message": "Settings updated successfully"}


# ==================== SYSTEM STATS ====================

@router.get("/stats/overview")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system-wide statistics."""
    total_crew = db.query(CrewMember).count()
    active_crew = db.query(CrewMember).filter(CrewMember.is_active == True).count()
    
    total_schedules = db.query(Schedule).count()
    active_schedules = db.query(Schedule).filter(Schedule.status == "active").count()
    
    total_assignments = db.query(ScheduleAssignment).count()
    
    return {
        "crew": {"total": total_crew, "active": active_crew},
        "schedules": {"total": total_schedules, "active": active_schedules},
        "assignments": total_assignments
    }


# ==================== AUDIT LOG ====================

@router.get("/audit/logs", response_model=List[SchedulingLog])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get audit logs for scheduling operations."""
    query = db.query(SchedulingLog).order_by(SchedulingLog.created_at.desc())
    
    if action_filter:
        query = query.filter(SchedulingLog.action == action_filter)
    
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": logs
    }


# ==================== USER MANAGEMENT ====================

@router.get("/users/", response_model=List[User])
async def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin_user)
):
    """List all users (admin only)."""
    return db.query(User).all()


@router.post("/users/", response_model=User)
async def create_user(
    user_data: User,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Create a new user."""
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db.add(user_data)
    db.commit()
    db.refresh(user_data)
    
    log_entry = SchedulingLog(
        action="user_created",
        details=f"User {user_data.email} created by {admin_user.email}"
    )
    db.add(log_entry)
    
    return user_data


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Delete a user."""
    if user_id == admin_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete admin")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


# ==================== INITIALIZATION ====================

@router.post("/init", response_model=dict)
async def initialize_system(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Initialize system with default settings."""
    
    # Ensure roles exist
    if not db.query(Role).filter(Role.name == "admin").first():
        RoleSeeder.ADMIN = Role(name="admin")
        db.add(RoleSeeder.ADMIN)
        db.commit()
        
        admin_user = User(
            email="admin@crew-scheduler.com",
            password_hash="hashed_password",  # Use proper hashing in production
            name="Administrator",
            role_id=RoleSeeder.ADMIN.id,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
    
    # Ensure constraints exist
    default_constraints = [
        Constraint(
            name="max_weekly_hours",
            description="Maximum weekly hours per crew member",
            value=40.0,
            enabled=True,
            priority=1
        ),
        Constraint(
            name="min_break_minutes",
            description="Minimum break duration in minutes",
            value=30.0,
            enabled=True,
            priority=2
        ),
        Constraint(
            name="max_consecutive_days",
            description="Maximum consecutive work days without rest",
            value=5.0,
            enabled=True,
            priority=1
        )
    ]
    
    for constraint in default_constraints:
        existing = db.query(Constraint).filter(Constraint.name == constraint.name).first()
        if not existing:
            db.add(constraint)
    
    db.commit()
    
    log_entry = SchedulingLog(
        action="system_initialized",
        details="System initialized with default constraints"
    )
    admin_user.id  # Trigger user load
    db.add(log_entry)
    
    return {
        "message": "System initialized successfully",
        "admin_email": "admin@crew-scheduler.com",
        "admin_password": "admin123"  # Change immediately in production!
    }