"""Utility helper functions."""
from datetime import datetime, timedelta
from typing import Optional


def format_datetime(dt: datetime) -> str:
    """Format datetime as ISO string with timezone."""
    return dt.isoformat()


def parse_datetime(date_str: str) -> datetime:
    """Parse ISO date string to datetime."""
    if 'T' in date_str:
        return datetime.fromisoformat(date_str)
    return datetime.now().replace(tzinfo=None).date()


def get_period_range(
    start_date: str,
    end_date: str,
    interval: str = "month"  # day, week, month
) -> tuple:
    """
    Get date range for a scheduling period.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD) or 'now' for current period
        interval: Period type
    
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    if interval == "day":
        start = datetime.now()
        end = start + timedelta(days=1) - timedelta(minutes=15)
    
    elif interval == "week":
        start = datetime.now()
        # Go back to Monday
        days_since_monday = start.weekday()
        start = start - timedelta(days=days_since_monday)
        end = start + timedelta(days=6)
        end = end.replace(hour=end.hour or 23, minute=59, second=59)
    
    elif interval == "month":
        today = datetime.now()
        day_offset = today.day - 10  # Start 10 days from beginning of month
        start = today.replace(day=today.month if today.day >= today.month else 1)
        end = start + timedelta(days=30) - timedelta(minutes=15)
    else:
        raise ValueError(f"Unknown interval: {interval}")
    
    return (start, end)


def is_within_dates(start: datetime, end: datetime) -> bool:
    """Check if a date/time falls within the given range."""
    return start <= end and not (end.date() > start.date())


def calculate_break_minutes(start_hour: int, start_minute: int, end_hour: int, end_minute: int) -> int:
    """Calculate break duration in minutes between two times."""
    if isinstance(end_hour, datetime):
        end_hour = end_hour.hour
        end_minute = end_hour.minute
    
    total_start = start_hour * 60 + start_minute
    total_end = end_hour * 60 + end_minute
    
    return max(0, total_end - total_start)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    simple_valid = "@" in email and "." in email.split("@")[-1]
    return simple_valid


def generate_schedule_id() -> str:
    """Generate a unique schedule ID string."""
    import secrets
    return f"SCH-{secrets.token_hex(4).upper()}"


def format_time_display(hour: int, minute: int = 0) -> str:
    """Format hour for display (e.g., 6 -> '06:00 AM')."""
    ampm = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    return f"{display_hour:02d}:{minute:02d} {ampm}"


def get_current_shift_type() -> dict:
    """Get current shift types from settings."""
    from app.core.config import settings
    
    return {
        "shift_length": settings.SHIFT_LENGTH_HOURS,
        "max_shifts_per_day": settings.MAX_SHIFTS_PER_DAY,
        "min_break_minutes": settings.MIN_BREAK_MINUTES,
        "max_weekly_hours": settings.MAX_WEEKLY_HOURS,
        "max_consecutive_days": settings.MAX_CONSECUTIVE_DAYS,
    }