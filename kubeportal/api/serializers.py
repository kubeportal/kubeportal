from rest_framework import serializers

class LoginSuccessSerializer(serializers.Serializer):
    """
    This is an override for the default answer to /login,
    as originally given by the dj_rest_auth library.
    The serializer is referenced in settings.py, accordingly.
    """

    def to_representation(self, instance):
        return {'id': instance['user'].pk,
                'firstname': instance['user'].first_name,
                'access_token': str(instance['access_token'])
                }

