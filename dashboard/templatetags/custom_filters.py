from django import template

register = template.Library()


@register.filter
def zip_lists(list1, list2):
    """Zips two lists together."""
    return zip(list1, list2)


register = template.Library()


@register.filter
def get_item(lst, index):
    return lst[int(index)] if 0 <= int(index) < len(lst) else None



