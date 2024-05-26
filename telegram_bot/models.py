from django.db import models


class User(models.Model):
    username = models.CharField('ФИО', max_length=100)
    telegram_id = models.PositiveBigIntegerField(
        'Внешний ID пользователя',
        unique=True
    )
    email = models.CharField(
        'Электронная почта',
        max_length=30,
        unique=True
    )
    phonenumber = models.CharField(
        'Телефон',
        max_length=20,
        unique=True
    )
    company = models.CharField(
        'Работодатель',
        max_length=200,
        null=True,
        blank=True
    )
    position = models.CharField(
        'Должность',
        max_length=100,
        null=True,
        blank=True
    )
    ROLE_CHOICES = [
        ('LISTENER', 'Слушатель'),
        ('SPEAKER', 'Спикер'),
        ('MANAGER', 'Организатор'),
    ]
    role = models.CharField(
        'Роль',
        max_length=50,
        choices=ROLE_CHOICES,
        default='LISTENER'
    )

    def __str__(self):
        return f'{self.telegram_id} {self.username}'

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'
        ordering = ['telegram_id']


class Event(models.Model):
    title = models.CharField('Тема мероприятия', max_length=100)
    program_description = models.TextField('Программа', blank=True)
    speaker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Спикер'
    )
    location = models.CharField('Место проведения', max_length=200)
    start_time = models.DateTimeField('Время начала')
    end_time = models.DateTimeField('Время окончания')
    image = models.ImageField(
        'Изображение',
        upload_to='image',
        blank=True
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'мероприятия'
        ordering = ['title']


class Question(models.Model):
    description = models.TextField('Вопрос к спикеру')
    status = models.BooleanField('Статус', default=False)
    listener = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question',
        verbose_name='Вопрос от слушателя'
    )
    speaker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answer',
        verbose_name='Ответ спикера'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        verbose_name='Вопрос мероприятия'
    )
    answer = models.TextField('Ответ', blank=True, null=True)


    def __str__(self):
        return self.description

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['description']


class Messages(models.Model):
    text = models.CharField('Содержание сообщения', max_length=200)
    participants = models.ManyToManyField(
        User,
        related_name='message',
        verbose_name='Участники рассылки'
    )
    created_at = models.DateTimeField(
        'Дата и время создания',
        auto_now_add=True
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['text']
