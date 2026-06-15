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
    months_back = random.randint(12, 14)
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


def is_under_18(date_str: str) -> bool:
    birth_date = parse_date(date_str)

    today = date.today()

    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age < 18


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
