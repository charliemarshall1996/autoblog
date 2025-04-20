
import csv

from django.db import models
from django.utils import timezone

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import MultiFieldPanel
from wagtail.search import index


def track_affiliate_click(blog_post_id, product_name, request):
    """
    Records an affiliate link click with request metadata
    """
    blog_post = BlogPage.objects.get(id=blog_post_id)

    AffiliateClick.objects.create(
        blog_post=blog_post,
        affiliate_product=product_name,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


def calculate_affiliate_revenue():
    """
    Integrate with your affiliate network API to get actual revenue data
    Example implementation for Amazon Associates:
    """
    # Placeholder - implement actual API integration
    return 0.0  # Replace with real revenue calculation


def generate_affiliate_report(days=30):
    """
    Generates a CSV/JSON report of affiliate performance
    """
    from datetime import timedelta
    from django.http import HttpResponse

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    clicks = AffiliateClick.objects.filter(
        click_time__range=(start_date, end_date)
    )

    # Simple CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="affiliate_report_{days}d.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Product', 'Clicks', 'Estimated Revenue'])

    for click in clicks:
        writer.writerow([
            click.click_time.date(),
            click.affiliate_product,
            1,  # Each row represents one click
            click.revenue or 0.0
        ])

    return response


def get_affiliate_stats(post_id=None):
    """
    Returns aggregated affiliate performance data
    """
    stats = {
        'total_clicks': 0,
        'clicks_last_30d': 0,
        'top_products': [],
        'revenue_last_30d': 0.0
    }

    now = timezone.now()

    if post_id:
        queryset = AffiliateClick.objects.filter(blog_post_id=post_id)
    else:
        queryset = AffiliateClick.objects.all()

    stats['total_clicks'] = queryset.count()
    stats['clicks_last_30d'] = queryset.filter(
        click_time__gte=now - timezone.timedelta(days=30)
    ).count()

    # Get top 5 performing products
    stats['top_products'] = list(
        queryset.values('affiliate_product')
        .annotate(total_clicks=models.Count('affiliate_product'))
        .order_by('-total_clicks')[:5]
    )

    # Calculate revenue (requires integration with affiliate network API)
    stats['revenue_last_30d'] = calculate_affiliate_revenue()

    return stats


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class BlogTagIndexPage(Page):

    def get_context(self, request):
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)

        context = super().get_context(request)
        context['blogpages'] = blogpages
        return context


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)
    # add the get_context method:

    def get_context(self, request):
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context

    content_panels = Page.content_panels + ["intro"]


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    thumbnail = models.ImageField(blank=True, null=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    # Add this:
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    # ... Keep the main_image method and search_fields definition. Then modify the content_panels:
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            "date",
            "tags",
        ], heading="Blog information"),
        "intro", "body", "gallery_images"
    ]

    affiliate_cta = models.TextField(
        blank=True, help_text="Auto-generated affiliate CTAs")

    def update_affiliate_performance(self):

        self.affiliate_clicks = get_affiliate_stats(self.id)
        self.save()

    def optimize_seo(self):
        # Implement actual SEO optimization logic
        self.search_description = self.body[:160]
        self.slug = '-'.join(self.title.lower().split()[:4])
        self.save()


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE,
                       related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = ["image", "caption"]


class AffiliateClick(models.Model):
    """
    Tracks clicks on affiliate links within blog posts
    """
    blog_post = models.ForeignKey(BlogPage, on_delete=models.CASCADE)
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
