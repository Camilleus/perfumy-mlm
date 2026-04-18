from django.db import models
from django.utils.text import slugify


class BlogPost(models.Model):
    title = models.CharField(max_length=200, verbose_name='Tytuł')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField(verbose_name='Treść')
    excerpt = models.TextField(max_length=300, blank=True, verbose_name='Zajawka')
    author_name = models.CharField(max_length=100, default='Marcel Krzeja', verbose_name='Autor')
    author_title = models.CharField(max_length=100, default='Założyciel & ekspert od zapachów', verbose_name='Tytuł autora')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True, verbose_name='Opublikowany')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Artykuł'
        verbose_name_plural = 'Artykuły'
        ordering = ['-created_at']