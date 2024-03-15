from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import RetrieveAPIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.permissions import IsAuthenticatedOrReadOnly


from main.models import Ad, Comment
from .serializers import AdSerializer, AdDetailSerializer, CommentSerializer

# Выдаем список объявлений
@api_view(['GET'])
def ads(request):
    if request.method == 'GET':
        ads = Ad.objects.filter(is_active=True)[:10]
        serializer = AdSerializer(ads, many=True)
        return Response(serializer.data)

# Выдаем сведения о выбранном объявлении
class AdDetailView(RetrieveAPIView):
    queryset = Ad.objects.filter(is_active=True)
    serializer_class = AdDetailSerializer

# Добавлять комментарий разрешено только зарегистрированным пользователям
# Просматривать комментарии разрешено всем
@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticatedOrReadOnly,))
def comments(request, pk):
    if request.method == 'POST':
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    else:
        comments = Comment.objects.filter(is_active=True, ad=pk)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
