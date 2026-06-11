import random
from datetime import date, timedelta, datetime


def year_month_str(d: date) -> str:
    return d.strftime("%Y-%m")


def iso_date_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def subtract_months(d: date, months: int) -> date:
    year, month = d.year, d.month - months
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def work_experience_begin_date(register_date: date) -> str:
    months_back = random.randint(12, 14)
    return year_month_str(subtract_months(register_date, months_back))


def work_experience_end_date() -> str:
    return year_month_str(date.today())


def monday_and_friday_skip_x_weeks(d: date, weeks: int, days: int):
    # Monday of the week that contains d
    monday = d - timedelta(days=d.weekday())   # weekday(): Mon=0..Sun=6
    # Skip 4 weeks forward
    monday += timedelta(weeks=weeks)
    friday = monday + timedelta(days=days)
    return monday, friday

def parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def format_date(date_text):
    return datetime.strptime(date_text, "%Y-%m-%d").strftime("%d.%m.%Y")


def get_today_parts():
    today = datetime.today()

    today_yyyy = today.strftime("%Y")
    today_mm = today.strftime("%m")
    today_dd = today.strftime("%d")

    return today_yyyy, today_mm, today_dd