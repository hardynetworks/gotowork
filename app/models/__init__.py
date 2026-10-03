"""Database models."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

# Associations
crew_member_shift = Table(
    'crew_member_shift',
    __base__,
    Column('crew_member_id', Integer, ForeignKey('crew_members.id'), primary_key=True),
    Column('shift_id', Integer, ForeignKey('shifts.id'), primary_key=True)
)


Base = declarative_base()


class Role(Base):
    """User roles."""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # admin, manager
    
    def __repr__(self):
        return f"<Role(name='{self.name}')>"


class User(Base):
    """System users."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: __import__('datetime').datetime.utcnow())
    
    role = relationship("Role", backref="users")
    
    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}')>"


class CrewMember(Base):
    """Crew team members to be scheduled."""
    __tablename__ = 'crew_members'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    skill_level = Column(String(50), default="general")  # general, advanced, specialist
    specializations = Column(Text)  # JSON-like text for multiple skills
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: __import__('datetime').datetime.utcnow())
    
    assigned_shifts = relationship("Shift", secondary=crew_member_shift, back_populates="crew_members")
    
    def __repr__(self):
        return f"<CrewMember(name='{self.name}')>"


class ShiftType(Base):
    """Available shift types (Morning, Evening, Night, etc.)."""
    __tablename__ = 'shift_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # morning, evening, night
    start_time = Column(Integer, nullable=False)  # hour (e.g., 6 for 6 AM)
    end_time = Column(Integer, nullable=False)  # hour (e.g., 14 for 2 PM)
    
    def __repr__(self):
        return f"<ShiftType(name='{self.name}', {self.start_time:02d}:00-{self.end_time:02d}:00)>"


class Shift(Base):
    """Scheduled shifts."""
    __tablename__ = 'shifts'
    
    id = Column(Integer, primary_key=True)
    shift_type_id = Column(Integer, ForeignKey('shift_types.id'), nullable=False)
    location = Column(String(100), nullable=False)  # e.g., "Store A", "Warehouse"
    start_date = Column(DateTime, index=True, nullable=False)
    end_date = Column(DateTime, nullable=False)
    description = Column(Text)
    
    shift_type = relationship("ShiftType", backref="shifts")
    crew_members = relationship("CrewMember", secondary=crew_member_shift, back_populates="assigned_shifts")
    
    def __repr__(self):
        return f"<Shift(location='{self.location}', {self.start_date.date()})>"


class Schedule(Base):
    """Complete schedule for a time period."""
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    period_start = Column(DateTime, index=True, nullable=False)
    period_end = Column(DateTime, index=True, nullable=False)
    location_id = Column(Integer, ForeignKey('shifts.id'), nullable=True)  # Specific shift location or null for all
    status = Column(String(20), default="draft")  # draft, active, completed
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: __import__('datetime').datetime.utcnow())
    
    creator = relationship("User", backref="schedules")
    
    def __repr__(self):
        return f"<Schedule({self.period_start.date()}-{self.period_end.date()})>"


class ScheduleAssignment(Base):
    """Individual assignments within a schedule."""
    __tablename__ = 'schedule_assignments'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
    crew_member_id = Column(Integer, ForeignKey('crew_members.id'), nullable=False)
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=False)
    assigned_at = Column(DateTime, default=lambda: __import__('datetime').datetime.utcnow())
    
    schedule = relationship("Schedule", backref="assignments")
    crew_member = relationship("CrewMember", backref="assignment")
    shift = relationship("Shift")
    
    def __repr__(self):
        return f"<Assignment(crew={self.crew_member.name})>"


class Constraint(Base):
    """Scheduling constraints (rules)."""
    __tablename__ = 'constraints'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # "max_weekly_hours", "consecutive_days"
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    value = Column(Float)  # Numeric constraint value
    priority = Column(Integer, default=1)  # Higher = stricter
    
    def __repr__(self):
        return f"<Constraint(name='{self.name}', value={self.value})>"


class SchedulingLog(Base):
    """Log of scheduling operations."""
    __tablename__ = 'scheduling_logs'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id'))
    action = Column(String(50), nullable=False)  # created, modified, generated, failed
    details = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: __import__('datetime').datetime.utcnow())


# Seed initial roles
class RoleSeeder:
    """Seed admin and manager roles."""
    
    ADMIN = Role(name="admin")
    MANAGER = Role(name="manager")