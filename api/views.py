from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from task.models import Task, User
from .mixins import CreateViewSet
from .permissions import IsAuthorOrReadOnly
from .serializers import UserSerializer, UserGetTokenSerializer, TaskSerializer


class UserViewSet(CreateViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], url_path='token')
    def get_token(self, request):
        serializer = UserGetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=serializer.validated_data['username']
        )
        if user.check_password(serializer.validated_data['password']):
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            data = {
                'token': token
            }
            return Response(data=data, status=status.HTTP_200_OK)
        raise serializers.ValidationError({'password': 'Неверный пароль'})


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'], url_path='my')
    def get_my_tasks(self, request):
        queryset = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
