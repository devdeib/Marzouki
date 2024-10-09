from django import template

register = template.Library()


@register.filter
def zip_lists(list1, list2):
    """Zips two lists together."""
    return zip(list1, list2)


register = template.Library()


@register.filter
def get_item(lst, index):
    return lst[index]
