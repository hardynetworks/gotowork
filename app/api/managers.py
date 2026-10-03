"""Manager API endpoints for crew scheduling."""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.scheduler import SchedulingEngine
from app.models import (
    CrewMember, ShiftType, Shift, Schedule, ScheduleAssignment,
    Role, User, Constraint, SchedulingLog
)


router = APIRouter(prefix="/managers", tags=["Managers"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ==================== CREW MEMBERS ====================

@router.post("/crew-members/", response_model=CrewMember)
async def create_crew_member(
    crew_data: CrewMember,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a new crew member."""
    # Check if email already exists
    existing = db.query(CrewMember).filter(CrewMember.email == crew_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate date range
    now = datetime.now().date()
    if crew_data.start_date and crew_data.start_date < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be in the past"
        )
    
    db_crew = CrewMember(**crew_data.dict())
    db.add(db_crew)
    db.commit()
    db.refresh(db_crew)
    
    log_entry = SchedulingLog(
        action="crew_member_created",
        details=f"Crew member {db_crew.name} created"
    )
    log_entry.user_id = user.id
    db.add(log_entry)
    
    return db_crew


@router.get("/crew-members/", response_model=List[CrewMember])
async def list_crew_members(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all crew members."""
    query = db.query(CrewMember).filter(CrewMember.is_active == True) if active_only else db.query(CrewMember)
    
    total = query.count()
    crew_members = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": crew_members
    }


@router.get("/crew-members/{crew_member_id}", response_model=CrewMember)
async def get_crew_member(
    crew_member_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get a specific crew member by ID."""
    crew_member = db.query(CrewMember).filter(CrewMember.id == crew_member_id).first()
    
    if not crew_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew member not found")
    
    return crew_member


@router.delete("/crew-members/{crew_member_id}")
async def delete_crew_member(
    crew_member_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a crew member."""
    crew_member = db.query(CrewMember).filter(CrewMember.id == crew_member_id).first()
    
    if not crew_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew member not found")
    
    db.delete(crew_member)
    db.commit()
    
    log_entry = SchedulingLog(
        action="crew_member_deleted",
        details=f"Crew member {crew_member.name} deleted"
    )
    log_entry.user_id = user.id
    db.add(log_entry)
    
    return {"message": "Crew member deleted successfully"}


# ==================== SHIFT TYPES ====================

@router.get("/shift-types/", response_model=List[ShiftType])
async def list_shift_types(db: Session = Depends(get_db)):
    """List all shift types (Morning, Evening, Night)."""
    return db.query(ShiftType).all()


@router.post("/shift-types/", response_model=ShiftType)
async def create_shift_type(shift_type: ShiftType, db: Session = Depends(get_db)):
    """Create a new shift type."""
    if db.query(ShiftType).filter(ShiftType.name == shift_type.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shift type already exists"
        )
    
    db.add(shift_type)
    db.commit()
    db.refresh(shift_type)
    return shift_type


# ==================== SCHEDULES ====================

@router.post("/schedules/", response_model=Schedule)
async def create_schedule(
    schedule_data: Schedule,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new schedule using the scheduling engine."""
    
    # Initialize scheduler
    scheduler = SchedulingEngine(db)
    
    # Generate schedule
    created_schedule = scheduler.generate_schedule(
        period_start=schedule_data.period_start,
        period_end=schedule_data.period_end,
        location_id=schedule_data.location_id,
        user_id=user.id
    )
    
    log_entry = SchedulingLog(
        schedule_id=created_schedule.id,
        action="created",
        details=f"Schedule created for period {schedule_data.period_start.date()} to {schedule_data.period_end.date()}"
    )
    log_entry.user_id = user.id
    db.add(log_entry)
    
    background_tasks.add_task(_notify_staff, created_schedule, user.email)
    
    return created_schedule


@router.get("/schedules/", response_model=List[Schedule])
async def list_schedules(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all schedules."""
    query = db.query(Schedule)
    
    if status_filter:
        query = query.filter(Schedule.status == status_filter)
    
    total = query.count()
    schedules = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": schedules
    }


@router.get("/schedules/{schedule_id}", response_model=Schedule)
async def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Get a specific schedule by ID."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    
    return schedule


@router.get("/schedules/{schedule_id}/statistics", response_model=dict)
async def get_schedule_statistics(
    schedule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get statistics for a schedule."""
    scheduler = SchedulingEngine(db)
    stats = scheduler.get_schedule_statistics(schedule_id)
    
    return stats


@router.post("/schedules/{schedule_id}/assign", response_model=dict)
async def assign_crew_to_shift(
    schedule_id: int,
    assignment_data: dict,  # {"crew_member_id": int, "shift_id": int}
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Manually assign a crew member to a shift."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    
    # Create assignment manually (bypasses scheduling engine)
    crew_member = db.query(CrewMember).filter(CrewMember.id == assignment_data["crew_member_id"]).first()
    shift = db.query(Shift).filter(Shift.id == assignment_data["shift_id"]).first()
    
    if not crew_member or not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    
    assignment = ScheduleAssignment(
        schedule_id=schedule_id,
        crew_member_id=crew_member.id,
        shift_id=shift.id
    )
    
    db.add(assignment)
    db.commit()
    
    log_entry = SchedulingLog(
        schedule_id=schedule_id,
        action="manual_assignment",
        details=f"Assigned {crew_member.name} to shift {shift.id}"
    )
    log_entry.user_id = user.id
    db.add(log_entry)
    
    return {"message": "Assignment created successfully"}


def _notify_staff(schedule: Schedule, user_email: str):
    """Background task to notify staff members about new schedule."""
    # In production, send email notifications
    print(f"NOTIFICATION: Sending schedule notification for {schedule.period_start.date()}")


# ==================== UTILITIES ====================

@router.get("/util/timezone", response_model=dict)
async def get_timezone_info():
    """Get timezone information for the current system."""
    import pytz
    from datetime import timezone
    
    return {
        "system_tz": pytz.timezone("America/Denver").name,
        "utc_offset": timezone.utc.utcoffset(None).total_seconds() / 3600,
        "current_time": datetime.now(timezone.utc).isoformat()
    }