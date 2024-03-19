from datetime import datetime


async def get_indicator(value: float,lower_limit: float,upper_limit: float) -> str:
    """Determine the indicator for the given value."""
    x = round(((value - lower_limit) / (upper_limit - lower_limit)) * 100,2)

    if x < 20:
        if x <= 0:
            return ("Very Low", 0)
        else:
            return ("Very Low", {x})
    elif 20 <= x < 40:
        return ("Low", {x})
    elif 40 <= x < 60:
        return ("Medium", {x})
    elif 60 <= x < 80:
        return ("High", {x})
    elif 80 <= x:
        if x <= 100:
            return ("Very High", {x})
        else:
            return ("Very High", 100)
    else:
        return ""


async def convert_to_datetime_format(year, month,date):
    if year or month:
        return datetime(int(year), int(month), int(date))
    return None

async def convert_to_datetime(year, month):
    if year or month:
        return datetime(int(year), int(month), 1)
    return None

async def convert_to_datetime_gap(date_str):
    return datetime.strptime(date_str, "%m-%Y")


async def get_ratio_indicator(x: float) -> str:
    """Determine the indicator for the given value."""

    if x < 50:
        return ("Excellent", {x})
    elif 50 <= x < 60:
        return ("Good", {x})
    elif 60 <= x < 80:
        return ("Concern", {x})
    elif 80 <= x:
        return ("Bad", {x})
    else:
        return ""
