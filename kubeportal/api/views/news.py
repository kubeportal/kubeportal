from rest_framework import serializers, generics

from kubeportal.models.news import News


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['title', 'content', 'author', 'created', 'modified', 'priority']


class NewsView(generics.ListAPIView):
    serializer_class = NewsSerializer
    queryset = News.objects.all()

