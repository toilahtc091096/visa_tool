import random
from datetime import date, timedelta, datetime
from typing import List, Dict, Union
import re


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
    months_back = random.randint(12, 24)
    return year_month_str(subtract_months(register_date, months_back))


def work_experience_end_date() -> str:
    return year_month_str(date.today())


def monday_and_friday_skip_x_weeks(d: date, x: int):
    # Monday of the week that contains d
    monday = d - timedelta(days=d.weekday())  # weekday(): Mon=0..Sun=6
    # Skip 4 weeks forward
    monday += timedelta(weeks=x)
    friday = monday + timedelta(days=x)
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


def age(date_str: str) -> int:
    birth_date = parse_date(date_str)

    today = date.today()

    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1

    return years


def is_under_18(date_str: str) -> bool:
    return age(date_str) < 18


def retirement_age_months(sex: str | None, year: int | None = None) -> int:
    """Legal retirement age in months for ``sex`` ("1"/"2") in ``year``."""
    from constants import (
        RETIREMENT_AGE_BASE_YEAR,
        RETIREMENT_AGE_FEMALE_MONTHS,
        RETIREMENT_AGE_MALE_MONTHS,
    )

    start, step, final = (
        RETIREMENT_AGE_FEMALE_MONTHS
        if str(sex or "").strip() == "2"
        else RETIREMENT_AGE_MALE_MONTHS
    )
    years_passed = max(0, (year or date.today().year) - RETIREMENT_AGE_BASE_YEAR)
    return min(start + step * years_passed, final)


def is_retired(date_str: str, sex: str | None) -> bool:
    """True when the age today has reached the retirement age for ``sex``."""
    birth_date = parse_date(date_str)
    if birth_date is None:
        return False
    today = date.today()
    age_months = (today.year - birth_date.year) * 12 + today.month - birth_date.month
    if today.day < birth_date.day:
        age_months -= 1
    return age_months >= retirement_age_months(sex, today.year)


# đang ở trong utils/date_util.py (hoặc module utils có date_util),
# nên gọi thẳng iso_date_str(...) không cần truyền date_util vào.


def build_three_stays(arrival_date: Union[date]) -> List[Dict[str, str]]:
    """
    Quy luật:
      - Chặng 1: 6 đêm  -> leave = arrival + 6 ngày
      - Chặng 2: 7 đêm  -> leave = arrival + 7 ngày
      - Chặng 3: 7 đêm  -> leave = arrival + 7 ngày
      - arrival chặng sau = leave chặng trước
    """
    nights = [6, 7, 7]
    stays: List[Dict[str, str]] = []

    cur_arrival = arrival_date
    for i, n in enumerate(nights, start=1):
        cur_leave = cur_arrival + timedelta(days=n)
        stays.append(
            {
                "sort": str(i),
                "arrivalDate": iso_date_str(cur_arrival),
                "leaveDate": iso_date_str(cur_leave),
            }
        )
        cur_arrival = cur_leave

    return stays


def get_end_date(start: date, duration: str) -> date:
    """
    duration ví dụ:
    3W1D
    2W6D
    4W
    10D
    """

    weeks = 0
    days = 0

    m = re.search(r"(\d+)W", duration)
    if m:
        weeks = int(m.group(1))

    m = re.search(r"(\d+)D", duration)
    if m:
        days = int(m.group(1))

    return start + timedelta(days=weeks * 7 + days)
