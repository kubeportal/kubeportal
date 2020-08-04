import os
from configurations import Configuration, values

from kubeportal.secret import get_secret_key


class Common(Configuration):
    VERSION = '0.3.14'

    SECRET_KEY = get_secret_key()

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'sortedm2m_filter_horizontal_widget',
        'oidc_provider',
        'social_django',
        'rest_framework',
        'rest_framework.authtoken',
        'multi_email_field',
        'kubeportal',
    ]

    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'kubeportal.middleware.AuthExceptionMiddleware'
    ]

    ROOT_URLCONF = 'kubeportal.urls'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'social_django.context_processors.backends',
                    'social_django.context_processors.login_redirect',
                ],
            },
        },
    ]

    REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'rest_framework.authentication.TokenAuthentication',
                ],
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticated',
                ]
            }

    WSGI_APPLICATION = 'kubeportal.wsgi.application'

    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    AUTHENTICATION_BACKENDS = (
        'social_core.backends.username.UsernameAuth',
        'django.contrib.auth.backends.ModelBackend',
        'social_core.backends.twitter.TwitterOAuth',
        'social_core.backends.google.GoogleOAuth2',
        'kubeportal.social.oidc.GenericOidc'
    )

    SOCIAL_AUTH_PIPELINE = (
        'kubeportal.social.ad.user_password',
        'kubeportal.social.ad.alt_mails',
        'social_core.pipeline.social_auth.social_details',
        'social_core.pipeline.social_auth.social_uid',
        'social_core.pipeline.social_auth.auth_allowed',
        'social_core.pipeline.social_auth.social_user',
        'social_core.pipeline.user.get_username',
        'social_core.pipeline.user.create_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.load_extra_data',
        'social_core.pipeline.user.user_details',
    )

    SOCIAL_AUTH_USERNAME_FORM_URL = '/login-form/'
    SOCIAL_AUTH_USERNAME_FORM_HTML = 'login_form.html'
    SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/welcome'
    LOGIN_REDIRECT_URL = '/welcome'
    SOCIAL_AUTH_LOGIN_ERROR_URL = '/'
    LOGIN_ERROR_URL = '/'
    LOGIN_URL = '/'
    LOGOUT_REDIRECT_URL = 'index'
    STATIC_URL = '/static/'

    USE_I18N = True
    USE_L10N = True
    USE_TZ = True

    CORS_ORIGIN_ALLOW_ALL = True

    ALLOWED_HOSTS = ['*']

    AUTH_USER_MODEL = 'kubeportal.User'
    SOCIAL_AUTH_USER_MODEL = 'kubeportal.User'

    OIDC_USERINFO = 'kubeportal.social.oidc.userinfo'
    OIDC_TEMPLATES = {
        'authorize': 'oidc_authorize.html',
        'error': 'oidc_error.html'
    }
    OIDC_IDTOKEN_INCLUDE_CLAIMS = True  # include user email etc. in token
    SESSION_COOKIE_DOMAIN = values.Value(None, environ_prefix='KUBEPORTAL')
    NAMESPACE_CLUSTERROLES = values.ListValue([], environ_prefix='KUBEPORTAL')

    SOCIAL_AUTH_TWITTER_KEY = values.Value(
        None, environ_name='AUTH_TWITTER_KEY', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_TWITTER_SECRET = values.Value(
        None, environ_name='AUTH_TWITTER_SECRET', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = values.Value(
        None, environ_name='AUTH_GOOGLE_KEY', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = values.Value(
        None, environ_name='AUTH_GOOGLE_SECRET', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GENERICOIDC_ENDPOINT = values.Value(
        None, environ_name='AUTH_OIDC_ENDPOINT', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GENERICOIDC_KEY = values.Value(
        None, environ_name='AUTH_OIDC_KEY', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GENERICOIDC_SECRET = values.Value(
        None, environ_name='AUTH_OIDC_SECRET', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GENERICOIDC_TITLE = values.Value(
        None, environ_name='AUTH_OIDC_TITLE', environ_prefix='KUBEPORTAL')
    AUTH_AD_DOMAIN = values.Value(None, environ_prefix='KUBEPORTAL')
    AUTH_AD_SERVER = values.Value(None, environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_SANITIZE_REDIRECTS = False   # let Django handle this

    API_SERVER_EXTERNAL = values.Value(None, environ_prefix='KUBEPORTAL')

    BRANDING = values.Value('KubePortal', environ_prefix='KUBEPORTAL')
    LANGUAGE_CODE = values.Value('en-us', environ_prefix='KUBEPORTAL')
    TIME_ZONE = values.Value('UTC', environ_prefix='KUBEPORTAL')

    ADMIN_NAME = values.Value(environ_prefix='KUBEPORTAL')
    ADMIN_EMAIL = values.Value(environ_prefix='KUBEPORTAL')
    ADMINS = [(str(ADMIN_NAME), str(ADMIN_EMAIL)), ]

    OIDC_AFTER_USERLOGIN_HOOK = 'kubeportal.security.oidc_login_hook'

class Development(Common):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, "static"),
    ]

    PROJECT_DIR = os.path.dirname(__file__)

    DEBUG = True

    REDIRECT_HOSTS = ['localhost', '127.0.0.1']

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST = values.Value('localhost', environ_prefix='KUBEPORTAL')

    ROOT_PASSWORD = values.Value('rootpw', environ_prefix='KUBEPORTAL')

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': "[%(asctime)s] %(levelname)s %(message)s"
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True
            },
            'KubePortal': {
                'handlers': ['console', ],
                'level': 'DEBUG',
                'propagate': True
            },
            'social': {
                'handlers': ['console', ],
                'level': 'DEBUG',
                'propagate': True
            },
        }
    }


class Production(Common):
    DEBUG = False

    DATABASE_URL = values.DatabaseURLValue(
        'sqlite:////data/kubeportal.sqlite3', environ_prefix='KUBEPORTAL')
    DATABASES = DATABASE_URL

    STATIC_ROOT = values.Value('', environ_prefix='KUBEPORTAL')
    STATICFILES_DIRS = values.TupleValue('', environ_prefix='KUBEPORTAL')

    REDIRECT_HOSTS = values.TupleValue(None, environ_prefix='KUBEPORTAL')

    EMAIL_HOST = values.Value('localhost', environ_prefix='KUBEPORTAL')

    LOG_LEVEL_PORTAL  = values.Value('ERROR', environ_prefix='KUBEPORTAL')
    LOG_LEVEL_SOCIAL  = values.Value('ERROR', environ_prefix='KUBEPORTAL')
    LOG_LEVEL_REQUEST = values.Value('ERROR', environ_prefix='KUBEPORTAL')
    
    # read the environment variables immediately because they're used to
    # configure the loggers below
    LOG_LEVEL_PORTAL.setup('LOG_LEVEL_PORTAL')
    LOG_LEVEL_SOCIAL.setup('LOG_LEVEL_SOCIAL')
    LOG_LEVEL_REQUEST.setup('LOG_LEVEL_REQUEST')
    
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': "[%(asctime)s] %(levelname)s %(message)s"
            },
        },
        'handlers': {
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
                'formatter': 'verbose'
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['mail_admins', 'console'],
                'level': LOG_LEVEL_REQUEST.value,
                'propagate': True
            },
            'KubePortal': {
                'handlers': ['mail_admins', 'console', ],
                'level': LOG_LEVEL_PORTAL.value,
                'propagate': True
            },
            'social': {
                'handlers': ['mail_admins', 'console', ],
                'level': LOG_LEVEL_SOCIAL.value,
                'propagate': True
            },
        }
    }
