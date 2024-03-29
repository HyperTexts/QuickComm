from django import template

from quickcomm.models import Post

register = template.Library()

@register.inclusion_tag("image.html", takes_context=True)
def image(context, post: Post):
    request = context["request"]
    url = post.get_image_url(request)
    return {"url": url}

