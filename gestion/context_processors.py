from django.conf import settings

def language_context(request):
    return {
        'LANGUAGES': settings.LANGUAGES,
        'LANGUAGE_CODE': request.LANGUAGE_CODE,
    }
