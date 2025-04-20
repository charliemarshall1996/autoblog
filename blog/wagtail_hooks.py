# blog/wagtail_hooks.py

from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from django_celery_beat.models import (
    CrontabSchedule,
    IntervalSchedule,
    ClockedSchedule,
    SolarSchedule,
    PeriodicTask,
)

#
# 1) Crontab schedules
#


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


# tells Wagtail to include this under “Snippets” :contentReference[oaicite:1]{index=1}
register_snippet(CrontabScheduleSnippet)

#
# 2) Interval schedules
#


class IntervalScheduleSnippet(SnippetViewSet):
    model = IntervalSchedule
    list_display = ("every", "period")
    panels = [
        FieldPanel("every"),
        FieldPanel("period"),
    ]


register_snippet(IntervalScheduleSnippet)

#
# 3) Clocked schedules
#


class ClockedScheduleSnippet(SnippetViewSet):
    model = ClockedSchedule
    list_display = ("clocked_time",)
    panels = [
        FieldPanel("clocked_time"),
    ]


register_snippet(ClockedScheduleSnippet)

#
# 4) Solar schedules
#


class SolarScheduleSnippet(SnippetViewSet):
    model = SolarSchedule
    list_display = ("event", "latitude", "longitude")
    panels = [
        FieldPanel("event"),
        FieldPanel("latitude"),
        FieldPanel("longitude"),
    ]


register_snippet(SolarScheduleSnippet)

#
# 5) Periodic tasks
#


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


register_snippet(PeriodicTaskSnippet)
