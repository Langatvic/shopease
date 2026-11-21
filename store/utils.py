from django.utils.text import slugify


def unique_slug(model, name, slug_field='slug'):
    slug = slugify(name)
    base_slug = slug
    counter = 1
    while model.objects.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug