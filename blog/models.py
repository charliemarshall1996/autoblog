
from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.admin.panels import FieldPanel
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import MultiFieldPanel
from wagtail.search import index

from . import blocks


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
    parent_page_types = ['blog.BlogIndexPage']
    affiliate_cta = models.TextField(
        blank=True, help_text="Auto-generated affiliate CTAs")

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


class Prompt(Orderable):
    SECTION_CHOICES = [
        ("T", "Title"),
        ("I", "Intro"),
        ("B", "Body"),
        ("C", "Conclusion"),
        ("A", "Action")
    ]
    prompt_text = models.TextField()
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)

    panels = [
        FieldPanel('section'),
        FieldPanel('prompt_text'),
    ]

    def __str__(self):
        return f"{self.get_section_display()}: {self.prompt_text[:50]}..."


class GenerationState(models.Model):
    last_affiliate = models.ForeignKey(
        'Affiliate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    last_keyword = models.ForeignKey(
        'Keyword',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )

    def __str__(self):
        return f"Last: {self.last_affiliate} / {self.last_keyword}"

    class Meta:
        verbose_name = "Generation State"
        verbose_name_plural = "Generation State"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
