from datetime import datetime, timezone


def format_relative_time(iso_string, now=None):
    if not iso_string:
        return ""
    try:
        timestamp = datetime.fromisoformat(str(iso_string).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        seconds = max(0, (current - timestamp).total_seconds())
        if seconds < 60:
            return "Just now"
        if seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        if seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        if seconds < 172800:
            return "Yesterday"
        if seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} days ago"
        return timestamp.strftime("%b %d")
    except (TypeError, ValueError, OverflowError):
        return ""


def unread_badge_label(count):
    value = max(0, int(count or 0))
    if value == 0:
        return None
    return "99+" if value > 99 else str(value)


def notification_destination(notification):
    notification_type = notification.get("type")
    if notification_type in {"like", "comment"}:
        return "post" if notification.get("post_id") else None
    if notification_type in {"friend_request", "friend_accept"}:
        return "friends"
    if notification_type == "message":
        return "chats"
    return None
