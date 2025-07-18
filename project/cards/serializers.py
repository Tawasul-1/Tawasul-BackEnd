from rest_framework import serializers
from cards.models import Category, Card, Board, Interaction
from users.models import User



class CategorySerializer(serializers.ModelSerializer):
    """ Serializer for Category model """
    class Meta:
        model = Category
        fields = ['id','image', 'name_en', 'name_ar']


class CardSerializer(serializers.ModelSerializer):
    """ Serializer for Card model """
    category = CategorySerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Card
        fields = [
            'id','image','title_en','title_ar','audio_en',
            'audio_ar','category','category_id'    
        ]


class BoardSerializer(serializers.ModelSerializer):
    """ Serializer for Board model """
    cards = CardSerializer(many=True, read_only=True)
    
    card_ids = serializers.PrimaryKeyRelatedField(
        queryset=Card.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Board
        fields = ['id', 'cards', 'card_ids']

    def update(self, instance, validated_data):
        card_ids = validated_data.pop('card_ids', None)
        if card_ids is not None:
            instance.cards.set(card_ids)
        instance.save()
        return instance
    
class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ['id', 'card', 'hour_range_start', 'hour_range_end', 'click_count']

    def create(self, validated_data):
        user = self.context['request'].user

        
        validated_data.pop('user', None)

        card = validated_data['card']
        hour_start = validated_data['hour_range_start']
        hour_end = validated_data['hour_range_end']
        click_count = validated_data['click_count']

        interaction, created = Interaction.objects.get_or_create(
            user=user,
            card=card,
            hour_range_start=hour_start,
            defaults={
                'hour_range_end': hour_end,
                'click_count': click_count,
            }
        )

        if not created:
            interaction.click_count += click_count
            interaction.hour_range_end = hour_end
            interaction.save()

        return interaction