import sys
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import send_mail
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from unidecode import unidecode
from django.template import defaultfilters

from django.urls import reverse
from PIL import Image


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """Функция создание учетной записи пользователя."""
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )
        user.slug = email[:email.find('@')]
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """Функция создание учетной записи сотрудника."""
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """Функция создание учетной записи суперпользователя."""

        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """Модель пользователя"""

    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(verbose_name='Активность',
                                    default=True)
    staff = models.BooleanField(verbose_name='Сотрудник',
                                default=False)  # a admin user; non super-user
    admin = models.BooleanField(verbose_name='Админ',
                                default=False)  # a superuser
    create_date = models.DateTimeField(verbose_name='Дата создания',
                                       auto_now_add=True)
    update_date = models.DateTimeField(verbose_name='Дата обновления',
                                       auto_now=True)
    signup_confirmed = models.BooleanField(verbose_name='Подтверждена регистрация',
                                           default=False)
    sex = models.ForeignKey('SexModel',
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            verbose_name='Пол')
    birthday = models.DateField(verbose_name='День рождения',
                                auto_now=False,
                                null=True,
                                blank=True)
    country = models.ForeignKey('CountryModel',
                                models.deletion.PROTECT,
                                null=True,
                                blank=True,
                                verbose_name='Страна')
    avatar = models.ImageField(upload_to="blog/avatar/%Y/%m/%d",
                               default="blog/avatar/default/default.png",
                               verbose_name='Аватар')
    slug = models.SlugField(max_length=255,
                            unique=True,
                            db_index=True,
                            verbose_name='URL')

    # notice the absence of a "Password field", that is built in.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email & Password are required by default.

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользоатель'
        verbose_name_plural = 'Пользователи'
        ordering = ['create_date', 'email']

    def get_absolute_url(self):
        return reverse('profile', kwargs={'url': self.slug})

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?
        Simplest possible answer: Yes, always"""
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?
        Simplest possible answer: Yes, always"""
        return True

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        return self.staff

    @property
    def is_admin(self):
        """Is the user a admin member?"""
        return self.admin


class SexModel(models.Model):
    """Модель пола"""
    name = models.CharField(max_length=20,
                            db_index=True,
                            verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Пол'
        verbose_name_plural = 'Полы'
        ordering = ['name']


class CountryModel(models.Model):
    """Модель названия стран"""
    name = models.CharField(max_length=50,
                            db_index=True,
                            verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'
        ordering = ['name', ]


class PostModel(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.PROTECT,
                               verbose_name='Автор')
    title = models.CharField(max_length=150,
                             verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст поста')
    datetime_create = models.DateTimeField(auto_now_add=True,
                                           verbose_name='Дата создания')
    datetime_update = models.DateTimeField(auto_now=True,
                                           verbose_name='Дата изменения')
    slug = models.SlugField(max_length=50,
                            db_index=True,
                            unique=True,
                            verbose_name='url',
                            allow_unicode=True)
    lon = models.FloatField(verbose_name='Широта')
    lat = models.FloatField(verbose_name='Долгота')
    tag = models.ManyToManyField('TagModel',
                                 db_index=True,
                                 verbose_name='Теги')
    emoji = models.ForeignKey('EmojisModel',
                              on_delete=models.PROTECT,
                              verbose_name='Emoji')

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['datetime_create', ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post', kwargs={'url': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = defaultfilters.slugify(unidecode(self.title))
        return super().save(*args, **kwargs)


class TagModel(models.Model):
    name = models.CharField(max_length=50,
                            unique=True,
                            verbose_name='Тег')
    slug = models.SlugField(unique=True,
                            db_index=True,
                            verbose_name='URL')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name', ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', kwargs={'url': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = defaultfilters.slugify(unidecode(self.name))
        return super().save(*args, **kwargs)


class ImagePostModel(models.Model):
    post = models.ForeignKey(PostModel,
                             on_delete=models.CASCADE,
                             verbose_name='Пост')
    image = models.ImageField(upload_to='blog/post/%Y/%m/%d',
                              verbose_name='Путь хранения')

    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фото'

    def __str__(self):
        return self.post.title

    def save(self, *args, **kwargs):
        image_temporary = Image.open(self.image)
        if image_temporary.mode != 'RGB':
            image_temporary = image_temporary.convert('RGB')
        output_io_stream = BytesIO()
        image_temporary.thumbnail((1280, 720), Image.ANTIALIAS)
        image_temporary.save(output_io_stream, format='JPEG', quality=75)
        output_io_stream.seek(0)
        self.image = InMemoryUploadedFile(output_io_stream, 'ImageField', "%s.jpg" % self.image.name.split('.')[0],
                                          'image/jpeg', sys.getsizeof(output_io_stream), None)
        super(ImagePostModel, self).save(*args, **kwargs)


class EmojisModel(models.Model):
    name = models.CharField(max_length=20,
                            verbose_name='Название emoji')
    emoji = models.ImageField(upload_to='blog/emoji/',
                              verbose_name='Путь хранения')
    slug = models.SlugField(unique=True,
                            db_index=True,
                            verbose_name='URL')

    class Meta:
        verbose_name = 'Emoji'
        verbose_name_plural = 'Emojis'

    def __str__(self):
        return self.emoji.url

    def get_absolute_url(self):
        return reverse('emoji', kwargs={'url': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = defaultfilters.slugify(unidecode(self.name))
        return super().save(*args, **kwargs)
