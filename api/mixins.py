from rest_framework import viewsets, mixins


class CreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    pass
