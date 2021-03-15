from rest_framework import serializers, generics
from rest_framework.reverse import reverse

from kubeportal.models.news import News


class NewsSerializer(serializers.ModelSerializer):
    author_url = serializers.URLField()

    class Meta:
        model = News
        fields = ['title', 'content', 'author_url', 'created', 'modified', 'priority']

    def to_representation(self, data):
        data = super(NewsSerializer, self).to_representation(data)
        request = self.context['request']
        author_url = reverse(viewname='user', kwargs={'user_id': data['author']}, request=request)
        data['author_url'] = author_url
        return data


class NewsView(generics.ListAPIView):
    serializer_class = NewsSerializer
    queryset = News.objects.all()

