from django.shortcuts import get_object_or_404, redirect
from django.http import HttpRequest
from . import models


def track_affiliate_click(request: HttpRequest):
    affiliate_id = request.GET.get('affiliate_id')
    product = request.GET.get('product')

    affiliate = get_object_or_404(models.Affiliate, id=affiliate_id)

    models.AffiliateClick.objects.create(
        affiliate=affiliate,
        affiliate_product=product or "Unknown",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    # Redirect to the actual affiliate link
    return redirect(affiliate.affiliate_link)


def get_client_ip(request: HttpRequest):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
