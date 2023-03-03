from django import template

register = template.Library()

@register.inclusion_tag('streamlike.html')
def streamlike(inbox_content):
    like = inbox_content.content_object
    time = inbox_content.added
    return {'like': like, 'time': time}

@register.inclusion_tag('streamcomment.html')
def streamcomment(inbox_content):
    comment = inbox_content.content_object
    time = inbox_content.added
    return {'comment': comment, 'time': time}

@register.inclusion_tag('streampost.html')
def streampost(inbox_content):
    post = inbox_content.content_object
    time = inbox_content.added
    return {'post': post, 'time': time}

@register.inclusion_tag('streamfollow.html')
def streamfollow(inbox_content):
    follow = inbox_content.content_object
    time = inbox_content.added
    return {'follow': follow, 'time': time}

@register.inclusion_tag('minipost.html')
def minipost(post):
    return {'post': post}