from django.db import models
from django.db import models
from gtts import gTTS
from datetime import datetime, timedelta, time

from users.models import User


class Category(models.Model):
    name_en = models.CharField(max_length=255,unique=True)
    name_ar = models.CharField(max_length=255,unique=True)

    def __str__(self):
        return self.name_en

class Card(models.Model):
    image = models.ImageField(upload_to='cards/')
    title_en = models.CharField(max_length=255, unique=True)
    title_ar = models.CharField(max_length=255, unique=True)
    audio_en = models.FileField(upload_to='audio/', blank=True, null=True)
    audio_ar = models.FileField(upload_to='audio/', blank=True, null=True)

    is_default = models.BooleanField(default=False)  


    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.audio_ar:
            ar_path = f'media/audio/{self.id}_ar.mp3'
            tts_ar = gTTS(text=self.title_ar, lang='ar')
            tts_ar.save(ar_path)
            self.audio_ar.name = f'audio/{self.id}_ar.mp3'

        if not self.audio_en:
            en_path = f'media/audio/{self.id}_en.mp3'
            tts_en = gTTS(text=self.title_en, lang='en')
            tts_en.save(en_path)
            self.audio_en.name = f'audio/{self.id}_en.mp3'

        super().save(update_fields=['audio_ar', 'audio_en'])

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='cards')


class Board(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='board')
    cards = models.ManyToManyField(Card, related_name='boards', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Board"
    

class Interaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    card = models.ForeignKey('Card', on_delete=models.CASCADE, related_name='interactions')
    timestamp = models.DateTimeField(auto_now_add=True)

    hour_range_start = models.TimeField()
    hour_range_end = models.TimeField()

    click_count = models.PositiveIntegerField(help_text="Total number of clicks")

    def save(self, *args, **kwargs):
        if not self.hour_range_start or not self.hour_range_end:
            now = datetime.now()
            hour_start = time(hour=now.hour)
            hour_end = (datetime.combine(now.date(), hour_start) + timedelta(hours=1)).time()

            self.hour_range_start = hour_start
            self.hour_range_end = hour_end

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.card.title_en} - {self.click_count} clicks from {self.hour_range_start} to {self.hour_range_end}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'card', 'hour_range_start'],
                name='unique_user_card_hour'
            )
        ]

