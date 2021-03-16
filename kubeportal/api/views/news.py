from rest_framework import serializers, generics
from rest_framework.reverse import reverse

from kubeportal.models.news import News


class NewsSerializer(serializers.ModelSerializer):
    author_url = serializers.URLField()

    class Meta:
        model = News
        fields = ['title', 'content', 'author_url', 'created', 'modified', 'priority']

    def to_representation(self, instance):
        request = self.context['request']
        instance.author_url = reverse(viewname='user', kwargs={'user_id': instance.author.pk}, request=request)
        data = super().to_representation(instance)
        return data


class NewsView(generics.ListAPIView):
    serializer_class = NewsSerializer
    queryset = News.objects.all()

