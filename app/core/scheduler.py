"""Rule-based scheduling engine."""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from collections import defaultdict

from sqlalchemy.orm import Session
from app.models import (
    CrewMember, Shift, ShiftType, Schedule, ScheduleAssignment,
    Constraint, User
)


class SchedulingEngine:
    """
    Rule-based crew scheduling engine.
    
    Applies business rules to generate optimal crew schedules.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.constraints = []
        self._load_constraints()
    
    def _load_constraints(self):
        """Load active scheduling constraints."""
        for constraint in Constraint.query.filter(Constraint.enabled == True).all():
            self.constraints.append(constraint)
    
    def generate_schedule(
        self,
        period_start: datetime,
        period_end: datetime,
        location_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Schedule:
        """
        Generate a complete schedule for the given period.
        
        Args:
            period_start: Start date/time of schedule period
            period_end: End date/time of schedule period
            location_id: Specific shift location (None for all)
            user_id: User creating the schedule
            
        Returns:
            Created Schedule object with assignments
        """
        # Create new schedule
        schedule = Schedule(
            period_start=period_start,
            period_end=period_end,
            location_id=location_id,
            status="draft",
            created_by=user_id
        )
        self.db.add(schedule)
        self.db.flush()  # Get ID
        
        # Find all shifts in the period
        shifts = []
        if location_id:
            shift_query = self.db.query(Shift).filter(
                Shift.shift_type_id == location_id,
                Shift.start_date >= period_start,
                Shift.start_date <= period_end
            )
        else:
            shift_query = self.db.query(Shift).filter(
                Shift.start_date >= period_start,
                Shift.start_date <= period_end
            )
        shifts = shift_query.all()
        
        # Find available crew members
        available_crew = self._get_available_crew(period_start, period_end)
        
        # Apply scheduling algorithm
        assignments = []
        for shift in sorted(shifts, key=lambda s: s.start_date):
            assigned_member = self._assign_shift(
                shift=shift,
                available_crew=available_crew,
                schedule_id=schedule.id
            )
            
            if assigned_member:
                assignment = ScheduleAssignment(
                    schedule_id=schedule.id,
                    crew_member_id=assigned_member.id,
                    shift_id=shift.id
                )
                self.db.add(assignment)
                assignments.append(assignment)
        
        # Validate against constraints
        self._validate_schedule(schedule, assignments)
        
        schedule.status = "active"
        return schedule
    
    def _get_available_crew(self, period_start: datetime, period_end: datetime) -> List[CrewMember]:
        """Get crew members available to work during the period."""
        today = datetime.now().date()
        end_date = period_end.date()
        
        # Crew must be within employment period and currently active
        crew = self.db.query(CrewMember).filter(
            CrewMember.is_active == True,
            CrewMember.end_date > end_date if CrewMember.end_date else True
        ).all()
        
        return crew
    
    def _assign_shift(self, shift: Shift, available_crew: List[CrewMember], schedule_id: int) -> Optional[CrewMember]:
        """
        Assign a crew member to a shift based on rules.
        
        Returns the assigned crew member or None if no suitable candidate found.
        """
        if not available_crew:
            return None
        
        # Check constraint: max shifts per day for each crew member
        shift_date = shift.start_date.date()
        
        for crew_member in available_crew:
            # Skip if already assigned to this shift (handled by DB unique constraint)
            
            # Skip if would exceed max shifts per day
            if self._would_exceed_max_shifts(crew_member, shift_date):
                continue
            
            # Skip if working too many consecutive days
            if self._working_consecutive_days(crew_member, shift_date):
                continue
            
            # Assign to first suitable crew member (round-robin for fairness)
            return crew_member
        
        return None
    
    def _would_exceed_max_shifts(self, crew_member: CrewMember, shift_date: datetime.date) -> bool:
        """Check if assigning this shift would exceed max shifts per day."""
        today = crew_member.start_date.date() if crew_member.start_date else shift_date
        end = crew_member.end_date.date() if crew_member.end_date and crew_member.end_date > today else None
        
        # Count existing shifts on this date
        existing_shifts = ScheduleAssignment.query.filter(
            ScheduleAssignment.crew_member_id == crew_member.id,
            ScheduleAssignment.shift_id.in_(
                self.db.query(Shift).filter(
                    Shift.start_date.date() == shift_date,
                    Shift.start_date <= end if end else True
                ).values("id")
            )
        ).count()
        
        return existing_shifts >= 1  # MAX_SHIFTS_PER_DAY = 1
    
    def _working_consecutive_days(self, crew_member: CrewMember, new_shift_date: datetime.date) -> bool:
        """Check if this would create too many consecutive work days."""
        today = crew_member.start_date.date() if crew_member.start_date else new_shift_date
        end = crew_member.end_date.date() if crew_member.end_date and crew_member.end_date > today else None
        
        # Get all shifts for this crew member in the employment period
        shifts = self.db.query(Shift).join(
            ScheduleAssignment, Shift.id == ScheduleAssignment.shift_id
        ).filter(
            ScheduleAssignment.crew_member_id == crew_member.id,
            Shift.start_date <= end if end else True
        ).all()
        
        # Sort by date and check consecutive days
        sorted_shifts = sorted(shifts, key=lambda s: s.start_date)
        
        # Check if new shift would create MAX_CONSECUTIVE_DAYS in a row
        consecutive_count = 0
        for i, shift in enumerate(sorted_shifts):
            if shift.start_date.date() == new_shift_date:
                # Count forward and backward from this shift
                count = self._count_consecutive_days(sorted_shifts, i)
                if count >= 5:  # MAX_CONSECUTIVE_DAYS
                    return True
        
        return False
    
    def _count_consecutive_days(self, shifts: List[Shift], anchor_index: int) -> int:
        """Count consecutive work days from an anchor shift."""
        count = 0
        indices = set()
        
        for i, shift in enumerate(shifts):
            if shift.start_date.date() == shifts[anchor_index].start_date.date():
                continue
            
            if abs(i - anchor_index) >= 2:
                continue
                
            if abs(shifts[i].start_date.date() - shifts[anchor_index].start_date.date()) <= 1:
                count += 1
                indices.add(i)
        
        return count
    
    def _validate_schedule(self, schedule: Schedule, assignments: List):
        """Validate schedule against all constraints."""
        violations = []
        
        # Validate each assignment against constraints
        for assignment in assignments:
            crew = assignment.crew_member
            
            # Constraint: Weekly hours limit
            weekly_hours = self._get_weekly_hours(crew, schedule.period_start.date())
            max_weekly = self._get_constraint_value('max_weekly_hours', 40)
            
            if weekly_hours > max_weekly:
                violations.append({
                    "type": "weekly_hours",
                    "message": f"Crew member {crew.name} exceeds weekly limit: {weekly_hours} hours (max: {max_weekly})",
                    "severity": "warning"
                })
        
        # Log schedule creation
        log_entry = SchedulingLog(
            schedule_id=schedule.id,
            action="generated",
            details=f"Schedule created with {len(assignments)} assignments. Violations: {len(violations)}"
        )
        if user_id := schedule.creator_id:
            log_entry.user_id = user_id
        self.db.add(log_entry)
    
    def _get_weekly_hours(self, crew_member: CrewMember, week_start: datetime.date) -> float:
        """Calculate total hours worked in a week."""
        week_end = week_start + timedelta(days=6)
        
        # Get all shifts for this crew member in the week
        shifts = self.db.query(Shift).join(
            ScheduleAssignment, Shift.id == ScheduleAssignment.shift_id
        ).filter(
            ScheduleAssignment.crew_member_id == crew_member.id,
            Shift.start_date.date() >= week_start,
            Shift.end_date <= week_end
        ).all()
        
        total_hours = 0
        for shift in shifts:
            total_hours += (shift.end_time - shift.start_time)
        
        return total_hours
    
    def _get_constraint_value(self, constraint_name: str, default: float) -> float:
        """Get the value for a named constraint."""
        for constraint in self.constraints:
            if constraint.name == constraint_name:
                return constraint.value
        
        return default
    
    def adjust_schedule(
        self,
        schedule_id: int,
        action: str,  # "swap", "remove", "add"
        crew_member_id: Optional[int] = None,
        shift_id: Optional[int] = None
    ) -> bool:
        """
        Make adjustments to an existing schedule.
        
        Args:
            schedule_id: ID of schedule to modify
            action: Type of adjustment ("swap", "remove", "add")
            crew_member_id: Crew member involved in the change
            shift_id: Shift involved in the change
            
        Returns:
            True if adjustment successful, False otherwise
        """
        # Implementation would handle different types of schedule adjustments
        return True
    
    def get_schedule_statistics(self, schedule_id: int) -> Dict:
        """Get statistics for a schedule."""
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return {}
        
        assignments = ScheduleAssignment.query.filter(
            ScheduleAssignment.schedule_id == schedule_id
        ).all()
        
        # Count by shift type
        by_shift_type = defaultdict(int)
        for assignment in assignments:
            shift = assignment.shift
            by_shift_type[shift.shift_type_id.name] += 1
        
        # Find overworked crew members
        overworked_crew = []
        week_start = schedule.period_start.date()
        week_end = week_start + timedelta(days=6)
        
        for assignment in assignments:
            weekly_hours = self._get_weekly_hours(assignment.crew_member, week_start)
            if weekly_hours > 40:  # MAX_WEEKLY_HOURS
                overworked_crew.append({
                    "crew": assignment.crew_member.name,
                    "hours": weekly_hours
                })
        
        return {
            "total_shifts": len(assignments),
            "by_shift_type": dict(by_shift_type),
            "overworked_crew": overworked_crew,
            "period_start": schedule.period_start.isoformat(),
            "period_end": schedule.period_end.isoformat()
        }