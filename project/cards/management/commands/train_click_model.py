from django.core.management.base import BaseCommand
from cards.models import Interaction
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import joblib
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Train a model to predict click count based on user, card, and hour'

    def handle(self, *args, **kwargs):
        # Load interaction data
        interactions = Interaction.objects.all()
        if not interactions.exists():
            self.stdout.write(self.style.WARNING("No interaction data found. Cannot train model."))
            return

        #  Prepare dataframe
        data = []
        for inter in interactions:
            data.append({
                'user_id': inter.user_id,
                'card_id': inter.card_id,
                'hour': inter.hour_range_start.hour,
                'click_count': inter.click_count
            })
        df = pd.DataFrame(data)

        #  Group by user/card/hour to combine clicks
        df = df.groupby(['user_id', 'card_id', 'hour'], as_index=False)['click_count'].sum()

        #  Encode user/card as categorical
        le_user = LabelEncoder()
        le_card = LabelEncoder()
        df['user_id'] = le_user.fit_transform(df['user_id'])
        df['card_id'] = le_card.fit_transform(df['card_id'])

        X = df[['user_id', 'card_id', 'hour']]
        y = df['click_count']

        #  Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        #  Save model + encoders as bundle
        model_dir = os.path.join(settings.BASE_DIR, 'cards', 'ml_models')
        os.makedirs(model_dir, exist_ok=True)

        bundle = {
            "model": model,
            "le_user": le_user,
            "le_card": le_card,
        }
        model_path = os.path.join(model_dir, 'click_model.pkl')
        joblib.dump(bundle, model_path)

        self.stdout.write(self.style.SUCCESS(f" Model trained and saved to {model_path}"))
