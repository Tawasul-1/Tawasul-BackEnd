import os
from django.conf import settings
from django.db import models
from django.db import models
import openai


from users.models import User


class Category(models.Model):
    image = models.ImageField(upload_to='cards/')
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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='cards')


    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        updated = False

        ar_path = f'media/audio/{self.id}_ar.mp3'
        en_path = f'media/audio/{self.id}_en.mp3'

        if not self.audio_ar:
            if self.generate_openai_tts(self.title_ar, 'ar', ar_path):
                self.audio_ar.name = f'audio/{self.id}_ar.mp3'
                updated = True

        if not self.audio_en:
            if self.generate_openai_tts(self.title_en, 'en', en_path):
                self.audio_en.name = f'audio/{self.id}_en.mp3'
                updated = True

        if updated:
            super().save(update_fields=['audio_ar', 'audio_en'])

    def generate_openai_tts(self, text, lang, save_path):
        try:
            openai.api_key = settings.OPENAI_API_KEY

            voice = 'onyx' 
            if lang == 'ar':
                voice = 'echo'  

            response = openai.audio.speech.create(
                model='tts-1',
                voice=voice,
                input=text
            )

            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'wb') as f:
                f.write(response.content)

            return True

        except Exception as e:
            print(f"Error generating TTS for {lang}: {e}")
            return False



class Board(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='board')
    cards = models.ManyToManyField(Card, related_name='boards', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Board"