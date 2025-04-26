from django.db import models
from django.utils import timezone

from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey

from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable


class Affiliate(ClusterableModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    website_url = models.URLField(blank=True, null=True)
    affiliate_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class AffiliateClick(models.Model):
    """
    Tracks clicks on affiliate links within blog posts
    """
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE)
    click_time = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    affiliate_product = models.CharField(max_length=255)
    revenue = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['-click_time']),
            models.Index(fields=['affiliate_product']),
        ]


class Keyword(Orderable):
    affiliate = ParentalKey(
        Affiliate,
        related_name="keywords",
        on_delete=models.CASCADE
    )
    keyword = models.CharField(max_length=255)

    panels = [
        FieldPanel('keyword'),
    ]

    def __str__(self):
        return self.keyword
