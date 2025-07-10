from django.db import models
from django.db import models
from gtts import gTTS


class Category(models.Model):
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)

    def __str__(self):
        return self.name_en

class Card(models.Model):
    image = models.ImageField(upload_to='cards/')
    title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255)
    audio_en = models.FileField(upload_to='audio/', blank=True, null=True)
    audio_ar = models.FileField(upload_to='audio/', blank=True, null=True)


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
