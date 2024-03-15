from rest_framework import serializers

from main.models import Ad, Comment


# Сериализатор, формирующий список объявлений
class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ('id', 'title', 'content', 'price', 'created_at')

# Сериализатор, выдающий сведения об объявлении
class AdDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ('id', 'title', 'content', 'price', 'created_at', 'contacts', 'image')

# Сериализатор, выдающий список комментариев и добавляющий новый комментарий
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('ad', 'author', 'content', 'created_at')
