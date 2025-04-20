# blog/tasks.py
import logging

from django.utils import timezone  # noqa
from django.conf import settings  # noqa

from transformers import pipeline
generator = pipeline(
    'text-generation', model=settings.AUTO_BLOG_MODEL_NAME, device=-1)  # noqa

from celery import shared_task  # noqa


from .models import BlogPage, BlogIndexPage  # noqa


# Get logger instance
logger = logging.getLogger(__name__)

# 2. Generate content from prompt


@shared_task(bind=True)
def generate_daily_blog_post(self):
    logger.info("Starting daily blog post generation")

    try:
        # 1. Build transformer prompt
        prompt = f"Write a detailed blog post about {settings.AFFILIATE_KEYWORDS}..."
        logger.debug(f"Using prompt: {prompt}")

        generated_content = generator(
            prompt, max_length=1500, do_sample=True, temperature=0.9
        )[0]['generated_text']

        logger.debug("Processed affiliate links")
        logger.info(f"Generated content: {generated_content[:100]}...")

        # 3. Process affiliate links
        logger.debug("Inserting affiliate links")
        for keyword in settings.AFFILIATE_KEYWORDS:
            processed_content = generated_content.replace(
                keyword, f"{keyword} [Affiliate Link]")

        # 4. Create BlogPage instance
        new_post = BlogPage(
            title=generated_content[:50] + "...",
            date=timezone.now(),
            intro=generated_content[:200] + "...",
            body=processed_content,
        )

        # 5. Attach to index
        index_page = BlogIndexPage.objects.first()
        if not index_page:
            logger.error("No BlogIndexPage found!")
            raise ValueError("Missing BlogIndexPage")

        index_page.add_child(instance=new_post)

        new_post.save_base()
        new_post.save_revision().publish()

        logger.info(f"Published new post: {new_post.title}")
        return f"Created post: {new_post.title}"

    except Exception as e:
        logger.exception("Failed to generate blog post")
        raise self.retry(exc=e, countdown=60)
