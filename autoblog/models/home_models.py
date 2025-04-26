
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class HeroBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    subheading = blocks.TextBlock(required=False)
    cta_text = blocks.CharBlock(required=False, default="Browse Posts")
    cta_link = blocks.PageChooserBlock(required=False)

    class Meta:
        icon = "title"
        label = "Hero Section"


class FeaturedPostBlock(blocks.StructBlock):
    posts = blocks.ListBlock(
        blocks.PageChooserBlock(target_model="blog.BlogPage"))

    class Meta:
        icon = "pick"
        label = "Featured Posts"


class CategoryBlock(blocks.StructBlock):
    name = blocks.CharBlock()
    link = blocks.PageChooserBlock(target_model="blog.BlogIndexPage")

    class Meta:
        icon = "list-ul"
        label = "Categories"


class ToolPromoBlock(blocks.StructBlock):
    tool_name = blocks.CharBlock()
    image = ImageChooserBlock()
    description = blocks.TextBlock()
    affiliate_link = blocks.URLBlock()

    class Meta:
        icon = "tag"
        label = "Affiliate Tool Promo"


class HomePage(Page):
    body = StreamField([
        ('hero', HeroBlock()),
        ('featured_posts', FeaturedPostBlock()),
        ('categories', blocks.ListBlock(CategoryBlock())),
        ('affiliate_tools', blocks.ListBlock(ToolPromoBlock())),
    ], use_json_field=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]
