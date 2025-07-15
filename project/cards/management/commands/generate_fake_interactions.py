from django.core.management.base import BaseCommand
from cards.models import Interaction
from users.models import User
from datetime import datetime, timedelta, time
import random


class Command(BaseCommand):
    help = 'Generate fake interaction data only for cards in user boards (merge duplicates)'

    def handle(self, *args, **kwargs):
        users = User.objects.prefetch_related("board__cards").all()
        created_count, updated_count = 0, 0

        for user in users:
            board = getattr(user, "board", None)
            if not board:
                continue

            cards = list(board.cards.all())
            if not cards:
                continue

            # لكل يوزر ٥ انتراكشنز (يمكن تعديل العدد)
            for _ in range(5):
                card = random.choice(cards)

                # ساعة عشوائية بين 8 صباحًا و 8 مساءً
                hour = random.randint(8, 20)
                hour_start = time(hour=hour)
                hour_end = (datetime.combine(datetime.today(), hour_start) + timedelta(hours=1)).time()
                clicks = random.randint(1, 10)

                # إذا وُجد صف بنفس (user, card, hour_start) نجمع الضغطات
                interaction, created = Interaction.objects.get_or_create(
                    user=user,
                    card=card,
                    hour_range_start=hour_start,
                    defaults={
                        "hour_range_end": hour_end,
                        "click_count": clicks
                    }
                )

                if created:
                    created_count += 1
                else:
                    interaction.click_count += clicks      # دمج الضغطات
                    interaction.hour_range_end = hour_end   # تحديث نهاية الساعة لو حابب
                    interaction.save(update_fields=["click_count", "hour_range_end"])
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {created_count} new interactions created, "
                f"{updated_count} existing interactions updated."
            )
        )
