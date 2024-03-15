from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save

from .utilities import get_timestamp_path, send_new_comment_notification

class AdvUser(AbstractUser):
    is_activated = models.BooleanField(default=True, db_index=True, verbose_name='Have you completed activation?')
    send_messages = models.BooleanField(default=True, verbose_name='Email notification about new comments?')
    
    # При удалении пользователя удаляем и его объявления
    def delete(self, *args, **kwargs):
        for ad in self.ad_set.all():
            ad.delete()
        super().delete(*args, **kwargs)

    class Meta(AbstractUser.Meta):
        pass

class Rubric(models.Model):
    # Базовая модель, в которой хранятся и главные рубрики, и подрубрики
    name = models.CharField(max_length=30, db_index=True, unique=True, verbose_name='Name')
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name='Sequence order')
    super_rubric = models.ForeignKey('SuperRubric', on_delete=models.PROTECT, null=True, blank=True, verbose_name='Main section')

class SuperRubricManager(models.Manager):
    # Обработка только главных рубрик
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=True)

class SuperRubric(Rubric):
    objects = SuperRubricManager()
    
    def __str__(self):
        # Метод генерит строковое название Главной рубрики
        return self.name

    class Meta:
        proxy = True
        ordering = ('order', 'name')
        verbose_name = 'Main section'
        verbose_name_plural = 'Main sections'

class SubRubricManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=False)

class SubRubric(Rubric):
    objects = SubRubricManager()
    
    def __str__(self):
        return '%s - %s' % (self.super_rubric.name, self.name)

    class Meta:
        proxy = True
        ordering = ('super_rubric__order', 'super_rubric__name', 'order', 'name')
        verbose_name = 'Subsections'
        verbose_name_plural = 'Subsections'

# Класс самих объявлений
class Ad(models.Model):
    rubric = models.ForeignKey(SubRubric, on_delete=models.PROTECT, verbose_name='Section') # Запрет каскадного удаления
    title = models.CharField(max_length=40, verbose_name='Product')
    content = models.TextField(verbose_name='Description')
    price = models.FloatField(default=0, verbose_name='Price')
    contacts = models.TextField(verbose_name='Contacts')
    image = models.ImageField(blank=True, upload_to=get_timestamp_path, verbose_name='Image')
    # разрешаем каскадное удаление. Т.е. при удалении объявления будут уничтожены все относящиеся к нему Дополнительные Изображения.
    # Это действие выполнит не Django, а СУБД. Т.е. физического удаления с диска файлов Изображений не произойдет.
    author = models.ForeignKey(AdvUser, on_delete=models.CASCADE, verbose_name='Ad author')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='Display in the ad list?')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Published')

    # Перед удалением текущей записи мы перебираем и вызовом метода delete() удаляем все связанные Дополнительные Изображения.
    # При вызове метода delete() возникает сигнал post_delete, обрабатываемый приложением django_cleanup, которое удалит файлы Изображений физически с диска.
    def delete(self, *args, **kwargs):
        for ai in self.additionalimage_set.all():
            ai.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Ads'
        verbose_name = 'Ad'
        ordering = ['-created_at']

# Класс Дополнительных изображений
class AdditionalImage(models.Model):
    # Объявление, к которому относится Изображение
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, verbose_name='Ad')
    image = models.ImageField(upload_to=get_timestamp_path, verbose_name='Image')

    class Meta:
        verbose_name_plural = 'Additional images'
        verbose_name = 'Additional image'

#Класс Комментариев
class Comment(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, verbose_name='Ads')
    author = models.CharField(max_length=30, verbose_name='Author')
    content = models.TextField(verbose_name='Comment')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='Display on screen?')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Published')

    class Meta:
        verbose_name_plural = 'Comments'
        verbose_name = 'Comment'
        ordering = ['created_at'] # Сортировка по увеличению временной отметки, т.е. более старые комментарии будут располагаться в начале списка, а более новые - в конце.

# Привяжем к сигналу post_save обработчик, вызывающий функцию send_new_comment_notification
# после добавления комментария
def post_save_dispatcher(sender, **kwargs):
    author = kwargs['instance'].ad.author
    if kwargs['created'] and author.send_messages:
        send_new_comment_notification(kwargs['instance'])

post_save.connect(post_save_dispatcher, sender=Comment)

