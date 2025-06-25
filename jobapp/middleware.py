from django.conf import settings
from django.http import HttpResponseForbidden

class IPWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        if ip not in getattr(settings, 'ALLOWED_IPS', []):
            return HttpResponseForbidden('Your IP is not allowed.')
        return self.get_response(request) 