# blog/tasks.py
import logging

from celery import shared_task

from django.utils import timezone
from django.conf import settings

from transformers import pipeline, AutoTokenizer
from transformers.generation import GenerationConfig

from . import models

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
