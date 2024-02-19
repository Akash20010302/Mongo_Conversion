from datetime import datetime


async def convert_to_datetime(year, month):
    if year or month:
        return datetime(int(year), int(month), 1)
    return None


async def convert_to_datetime_gap(date_str):
    return datetime.strptime(date_str, "%m-%Y")


async def overlap(start1, end1, start2, end2):
    return (await convert_to_datetime_gap(start1)) <= (
        await convert_to_datetime_gap(end2)
    ) and (await convert_to_datetime_gap(start2)) <= (
        await convert_to_datetime_gap(end1)
    )
