from datetime import datetime

def days_between(start_date: str, end_date: str) -> int:
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    return (end - start).days + 1

