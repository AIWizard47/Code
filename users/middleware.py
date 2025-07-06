from django.http import HttpResponseForbidden

# Example blocked IPs
BLOCKED_IPS = {
    "203.0.113.45",
    "198.51.100.23",
    "192.0.2.5",
    # add more IPs you want to block
}

class BlockBadIPsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        if ip in BLOCKED_IPS:
            return HttpResponseForbidden("Access denied: your IP has been blocked.")
        return self.get_response(request)
