from datetime import timedelta


def timedelta_to_cron(td: timedelta) -> str:
    """
    Convert a timedelta object to an approximate cron expression.

    Args:
        td (timedelta): The timedelta object to convert.

    Returns:
        str: An approximate cron expression.

    Raises:
        ValueError: If the timedelta cannot be converted to a simple cron expression.
    """
    minutes = td.total_seconds() / 60
    hours = minutes / 60
    days = td.days

    if days == 0:
        if minutes == 1:
            return "* * * * *"  # Every minute
        elif minutes == 30:
            return "*/30 * * * *"  # Every 30 minutes
        elif hours == 1:
            return "0 * * * *"  # Every hour
        elif hours == 2:
            return "0 */2 * * *"  # Every 2 hours
        elif hours == 3:
            return "0 */3 * * *"  # Every 3 hours
        elif hours == 4:
            return "0 */4 * * *"  # Every 4 hours
        elif hours == 6:
            return "0 */6 * * *"  # Every 6 hours
        elif hours == 12:
            return "0 */12 * * *"  # Every 12 hours
    elif days == 1:
        return "0 0 * * *"  # Every day at midnight
    elif days == 7:
        return "0 0 * * 0"  # Every week on Sunday at midnight

    raise ValueError("Cannot convert this timedelta to a simple cron expression")
