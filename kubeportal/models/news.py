from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from tinymce.models import HTMLField

from . import User

class News(models.Model):
    """
    News on the portal front page.
    """
    title = models.CharField(null=False, max_length=40)
    content = HTMLField()
    author = models.ForeignKey(User, related_name="news", on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(validators=[MinValueValidator(0),
                                               MaxValueValidator(2)],
                                   default=0)

    class Meta:
        verbose_name_plural = 'news'

    def __str__(self):
        return f"News from {self.modified.strftime('%m/%d/%Y')}"
