
from ...affiliate import models
from wagtail.admin import panels
from wagtail.snippets.views import snippets


class AffiliateSnippet(snippets.SnippetViewSet):
    model = models.Affiliate
    menu_label = "Affiliates"
    menu_icon = "group"
    list_display = ("name", "description", "website_url", "affiliate_link")
    search_fields = ("name", "description")

    # Define panels here to avoid circular imports
    panels = [
        panels.FieldPanel("name"),
        panels.FieldPanel("description"),
        panels.FieldPanel("website_url"),
        panels.FieldPanel("affiliate_link"),
        panels.InlinePanel("keywords", heading="Keywords", label="Keyword"),
        panels.InlinePanel("prompts", heading="Prompts", label="Prompt"),
    ]
