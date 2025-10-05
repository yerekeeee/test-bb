from django import template

register = template.Library()


@register.filter
def format_duration(duration):
    """Форматирует timedelta в 'X час Y мин' или 'Y мин'."""
    if not duration:
        return ""
    total_minutes = int(duration.total_seconds() / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0 and minutes > 0:
        return f"{hours} час {minutes} мин"
    elif hours > 0:
        return f"{hours} час"
    else:
        return f"{minutes} мин"


# ▼▼▼ ДОБАВЬТЕ ЭТУ ФУНКЦИЮ ▼▼▼
@register.filter
def get_item(dictionary, key):
    """Позволяет получать значение из словаря по ключу в шаблоне."""
    return dictionary.get(key)