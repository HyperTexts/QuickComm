
# Taken from https://github.com/agusmakmun/django-markdown-editor/issues/120#issuecomment-659306021
# to solve the issue with CSRF token using martor
def no_csfr(get_response):
    def middleware(request):

        if "martor" in request.path:
            setattr(request, "_dont_enforce_csrf_checks", True)

        response = get_response(request)

        return response

    return middleware