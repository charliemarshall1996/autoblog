# blog/tasks.py
import logging

from celery import shared_task

from django.utils import timezone
from django.conf import settings

from transformers import pipeline, AutoTokenizer
from transformers.generation import GenerationConfig

from .models import BlogPage, BlogIndexPage
from .wagtail_hooks import GenerationState, Affiliate

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug messages are captured

try:
    logger.debug("Initializing tokenizer with model: %s",
                 settings.AUTO_BLOG_MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(settings.AUTO_BLOG_MODEL_NAME)
    if tokenizer.pad_token is None:
        logger.debug("No pad_token found, setting to eos_token or [PAD]")
        tokenizer.pad_token = tokenizer.eos_token or "[PAD]"
except Exception as e:
    logger.error(f"Failed to initialize tokenizer: {str(e)}")
    raise

logger.debug("Setting tokenizer padding_side to 'left'")
tokenizer.padding_side = "left"

logger.debug("Initializing text-generation pipeline")
generator = pipeline(
    'text-generation',
    model=settings.AUTO_BLOG_MODEL_NAME,
    device=-1,
    tokenizer=tokenizer,
    truncation=True,
    padding='max_length',
    generation_kwargs={
        'return_full_text': False,
        'clean_up_tokenization_spaces': True,
        'stop_sequence': ['\n\n', '##', '---']
    }
)
logger.debug("Text-generation pipeline initialized successfully")

body_generation_config = GenerationConfig(
    max_new_tokens=400,
    min_new_tokens=50,
    do_sample=True,
    temperature=0.7,
    top_k=50,
    top_p=0.95,
    num_beams=3,
    early_stopping=True,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.eos_token_id
)
logger.debug("Body generation config created: %s", body_generation_config)

title_generation_config = GenerationConfig(
    max_new_tokens=15,
    min_new_tokens=5,
    do_sample=True,
    temperature=0.7,
    top_k=20,
    top_p=0.85,
    num_beams=3,
    no_repeat_ngram_size=2,
    early_stopping=True,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.eos_token_id,
    length_penalty=1.5,
    repetition_penalty=1.2
)
logger.debug("Title generation config created: %s", title_generation_config)


def clean_generated_text(text):
    logger.debug("Cleaning generated text: %s",
                 text[:100] + "..." if len(text) > 100 else text)
    if '.' in text:
        logger.debug("Found period in text, splitting at last sentence")
        text = text.rsplit('.', 1)[0] + '.'
    logger.debug("Stripping trailing whitespace")
    return text.strip()


def generate_with_sentence_boundaries(prompt_text, max_new_tokens=300, config=body_generation_config):
    logger.debug("Generating text with sentence boundaries for prompt: %s",
                 prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text)
    logger.debug("Max new tokens: %d, Config: %s", max_new_tokens, config)

    max_output_length = max_new_tokens + len(prompt_text) // 2
    config.max_new_tokens = max_output_length
    generator.generation_config = config

    logger.debug("Tokenizing input")
    inputs = tokenizer.tokenize(prompt_text, return_tensors="pt",
                                padding=True, truncation=True)

    logger.debug("Generating text")
    outputs = generator(inputs)
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logger.debug("Raw generated text: %s",
                 generated[:200] + "..." if len(generated) > 200 else generated)

    # Find last complete sentence
    last_period = generated.rfind('.')
    last_question = generated.rfind('?')
    last_exclamation = generated.rfind('!')
    end_pos = max(last_period, last_question, last_exclamation)

    if end_pos > 0:
        logger.debug("Found sentence boundary at position %d", end_pos)
        return generated[:end_pos+1]

    logger.debug("No sentence boundary found, returning full generated text")
    return generated


def generate_by_paragraphs(prompt_text, paragraphs=3):
    logger.debug("Generating by paragraphs (count: %d) for prompt: %s",
                 paragraphs, prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text)
    full_text = ""
    for i in range(paragraphs):
        logger.debug("Generating paragraph %d/%d", i+1, paragraphs)
        chunk = generate_with_sentence_boundaries(
            prompt_text + full_text,
            max_new_tokens=100
        )
        logger.debug("Generated chunk %d: %s", i+1,
                     chunk[:200] + "..." if len(chunk) > 200 else chunk)
        full_text += "\n\n" + chunk.split(prompt_text)[-1].strip()
    logger.debug("Completed paragraph generation")
    return prompt_text + full_text


def is_coherent(clean_text, min_sentences=2):
    logger.debug("Checking coherence for text: %s",
                 clean_text[:200] + "..." if len(clean_text) > 200 else clean_text)
    sentences = [s.strip() for s in clean_text.split('.') if s.strip()]
    logger.debug("Found %d sentences: %s", len(sentences), sentences)
    coherence = len(sentences) >= min_sentences and all(
        len(s.split()) > 3 for s in sentences)
    logger.debug("Coherence check result: %s", coherence)
    return coherence


def generate_coherent_text(
    prompt_text: str,
    max_attempts: int = 3,
    current_attempt: int = 1,
    **generation_kwargs
) -> str:
    logger.debug("Generating coherent text (attempt %d/%d) for prompt: %s",
                 current_attempt, max_attempts, prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text)
    logger.debug("Generation kwargs: %s", generation_kwargs)

    generated_text = generate_with_sentence_boundaries(
        prompt_text,
        max_new_tokens=generation_kwargs.get('max_length', 300),
        config=generation_kwargs.get('config', body_generation_config)
    )
    logger.debug("Generated text (pre-clean): %s",
                 generated_text[:200] + "..." if len(generated_text) > 200 else generated_text)

    clean_text = clean_generated_text(generated_text)
    logger.debug("Cleaned text: %s",
                 clean_text[:200] + "..." if len(clean_text) > 200 else clean_text)

    if is_coherent(clean_text):
        logger.debug("Text is coherent, returning")
        return clean_text

    if current_attempt < max_attempts:
        logger.warning(
            f"Text coherence check failed (attempt {current_attempt}). Regenerating..."
        )
        return generate_coherent_text(
            prompt_text,
            max_attempts=max_attempts,
            current_attempt=current_attempt + 1,
            **generation_kwargs
        )

    logger.error(
        "Max regeneration attempts reached. Returning best available.")
    return clean_text


@shared_task(bind=True)
def generate_daily_blog_post(self):
    logger.info("Starting daily blog post generation")

    try:
        logger.debug("Retrieving or creating GenerationState")
        state, _ = GenerationState.objects.get_or_create(id=1)
        logger.debug("Generation state: %s", state)

        logger.debug("Retrieving affiliates ordered by ID")
        affiliates = list(Affiliate.objects.order_by('id'))
        n_affiliates = len(affiliates)
        logger.debug("Found %d affiliates: %s", n_affiliates,
                     [a.name for a in affiliates])

        if not affiliates:
            logger.warning("No affiliates retrieved. Exiting.")
            return

        current_aff_index = 0
        if state.last_affiliate:
            logger.debug("Last affiliate found in state: %s (ID: %d)",
                         state.last_affiliate.name, state.last_affiliate.id)
            for i, a in enumerate(affiliates):
                if a.id == state.last_affiliate.id:
                    current_aff_index = i
                    break
        logger.debug("Current affiliate index: %d", current_aff_index)

        current_affiliate = affiliates[current_aff_index]
        logger.debug("Current affiliate: %s (ID: %d)",
                     current_affiliate.name, current_affiliate.id)

        logger.debug("Retrieving keywords for current affiliate")
        keywords = list(current_affiliate.keywords.order_by('id'))
        n_keywords = len(keywords)
        logger.debug("Found %d keywords: %s", n_keywords,
                     [k.keyword for k in keywords])

        if not keywords:
            logger.warning("No keywords found for affiliate %s",
                           current_affiliate.name)
            return

        current_key_index = 0
        if state.last_keyword:
            logger.debug("Last keyword found in state: %s (ID: %d)",
                         state.last_keyword.keyword, state.last_keyword.id)
            for i, k in enumerate(keywords):
                if k.id == state.last_keyword.id:
                    current_key_index = i + 1
                    break

        logger.debug("Current keyword index: %d", current_key_index)

        if current_key_index >= len(keywords):
            logger.debug(
                "Keyword index exceeds available keywords, moving to next affiliate")
            current_aff_index = (current_aff_index + 1) % len(affiliates)
            current_affiliate = affiliates[current_aff_index]
            logger.debug("New current affiliate: %s (ID: %d)",
                         current_affiliate.name, current_affiliate.id)
            keywords = list(current_affiliate.keywords.order_by('id'))
            current_key_index = 0
            logger.debug("Reset keyword index to 0 for new affiliate")

        if not keywords:
            logger.warning(
                "No keywords found for new affiliate %s", current_affiliate.name)
            return

        current_keyword = keywords[current_key_index]
        logger.debug("Current keyword: %s (ID: %d)",
                     current_keyword.keyword, current_keyword.id)

        logger.debug("Retrieving prompts for affiliate")
        prompts = current_affiliate.prompts.all()
        logger.debug("Found %d prompts: %s", len(
            prompts), [p.section for p in prompts])

        blog_content = []
        sections = {
            'title_prompt_text': None,
            'intro': None,
            'intro_prompt': True
        }

        for prompt in prompts:
            logger.debug("Processing prompt for section: %s", prompt.section)
            prompt_text = prompt.prompt_text.replace(
                "{affiliate}", current_affiliate.name).replace("{keyword}", current_keyword.keyword)
            logger.debug("Processed prompt text: %s",
                         prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text)

            if prompt.section != 'T':
                logger.debug("Generating content for non-title section")
                coherent_text = generate_coherent_text(
                    prompt_text, max_attempts=5)
                logger.debug("Generated coherent text for section %s: %s",
                             prompt.section, coherent_text[:200] + "..." if len(coherent_text) > 200 else coherent_text)

                if sections.get('intro_prompt'):
                    logger.debug("Setting intro section text")
                    sections['intro'] = coherent_text
                    sections['intro_prompt'] = False

                blog_content.append(coherent_text)
            else:
                logger.debug("Setting title prompt text")
                sections['title_prompt_text'] = prompt_text

        full_post = "\n\n".join(blog_content)
        logger.debug("Full post content (pre-link processing): %s",
                     full_post[:500] + "..." if len(full_post) > 500 else full_post)

        logger.debug("Generating title")
        post_title = generate_coherent_text(
            sections['title_prompt_text'], max_attempts=5, config=title_generation_config)
        logger.debug("Generated title: %s", post_title)

        logger.debug("Processing affiliate links")
        processed_content = full_post
        for keyword in settings.AFFILIATE_KEYWORDS:
            logger.debug("Processing keyword: %s", keyword)
            processed_content = processed_content.replace(
                keyword, f"{keyword} [Affiliate Link]")
        logger.debug("Content after link processing: %s",
                     processed_content[:500] + "..." if len(processed_content) > 500 else processed_content)

        logger.debug("Creating new BlogPage instance")
        new_post = BlogPage(
            title=post_title,
            date=timezone.now(),
            intro=sections['intro'],
            body=processed_content,
        )
        logger.debug("BlogPage instance created: %s", new_post)

        logger.debug("Retrieving BlogIndexPage")
        index_page = BlogIndexPage.objects.first()
        if not index_page:
            logger.error("No BlogIndexPage found!")
            raise ValueError("Missing BlogIndexPage")
        logger.debug("Found BlogIndexPage: %s", index_page)

        logger.debug("Saving new post")
        new_post.save()
        logger.debug("Post saved with ID: %d", new_post.id)

        logger.debug("Adding post as child to index page")
        try:
            index_page.add_child(instance=new_post)
            logger.debug("Post added as child successfully")
        except AttributeError as e:
            if "'NoneType' object has no attribute '_inc_path'" in str(e):
                logger.debug("Handling case where index page has no children")
                new_post.path = index_page.path + '0001'
                new_post.depth = index_page.depth + 1
                new_post.save()
                logger.debug("Post saved with manual path: %s", new_post.path)
            else:
                logger.error("Error adding child: %s", str(e))
                raise

        logger.debug("Publishing post revision")
        new_post.save_revision().publish()
        logger.info("Published new post: %s (ID: %d)",
                    new_post.title, new_post.id)

        return f"Created post: {new_post.title}"

    except Exception as e:
        logger.exception("Failed to generate blog post: %s", str(e))
        raise self.retry(exc=e, countdown=60)

    finally:
        logger.debug("Resetting generator config to body_generation_config")
        generator.generation_config = body_generation_config
        logger.debug("Daily blog post generation task completed")
