# blog/wagtail_hooks.py

from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from django_celery_beat.models import (
    CrontabSchedule,
    IntervalSchedule,
    ClockedSchedule,
    SolarSchedule,
    PeriodicTask,
)


class CrontabScheduleSnippet(SnippetViewSet):
    model = CrontabSchedule
    list_display = ("minute", "hour", "day_of_week",
                    "day_of_month", "month_of_year")
    panels = [
        FieldPanel("minute"),
        FieldPanel("hour"),
        FieldPanel("day_of_week"),
        FieldPanel("day_of_month"),
        FieldPanel("month_of_year"),
    ]


class IntervalScheduleSnippet(SnippetViewSet):
    model = IntervalSchedule
    list_display = ("every", "period")
    panels = [
        FieldPanel("every"),
        FieldPanel("period"),
    ]


class ClockedScheduleSnippet(SnippetViewSet):
    model = ClockedSchedule
    list_display = ("clocked_time",)
    panels = [
        FieldPanel("clocked_time"),
    ]


class SolarScheduleSnippet(SnippetViewSet):
    model = SolarSchedule
    list_display = ("event", "latitude", "longitude")
    panels = [
        FieldPanel("event"),
        FieldPanel("latitude"),
        FieldPanel("longitude"),
    ]


class PeriodicTaskSnippet(SnippetViewSet):
    model = PeriodicTask
    list_display = (
        "name",
        "task",
        "enabled",
        "last_run_at",
        "total_run_count",
    )
    panels = [
        FieldPanel("name"),
        FieldPanel("task"),
        FieldPanel("crontab"),
        FieldPanel("interval"),
        FieldPanel("clocked"),
        FieldPanel("solar"),
        FieldPanel("args"),
        FieldPanel("kwargs"),
        FieldPanel("enabled"),
    ]


class SchedulingSnippetGroup(SnippetViewSetGroup):
    items = (CrontabScheduleSnippet, IntervalScheduleSnippet,
             ClockedScheduleSnippet, SolarScheduleSnippet, PeriodicTaskSnippet)
    menu_icon = "calendar-check"
    menu_label = "Scheduling"
    menu_name = "scheduling"


"""class GenerationStateSnippet(SnippetViewSet):
    model = GenerationState
    list_display = (
        "last_affiliate",
        "last_keyword"
    )
    panels = [
        FieldPanel("last_affiliate"),
        FieldPanel("last_keyword"),
    ]
"""

"""class SetupSnippetGroup(SnippetViewSetGroup):
    items = (GenerationStateSnippet)
    menu_icon = "cogs"
    menu_label = "Setup"
    menu_name = "setup"""


register_snippet(SchedulingSnippetGroup)
"register_snippet(SetupSnippetGroup)"
