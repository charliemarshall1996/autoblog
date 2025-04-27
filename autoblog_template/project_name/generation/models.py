from django.db import models

from wagtail.models import Orderable
from wagtail.admin import panels
# Create your models here.


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
        panels.FieldPanel('section'),
        panels.FieldPanel('prompt_text'),
    ]

    def __str__(self):
        return f"{self.get_section_display()}: {self.prompt_text[:50]}..."
