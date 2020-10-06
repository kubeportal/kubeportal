import os
from urllib.parse import urlparse
from configurations import Configuration, values
from kubeportal.secret import get_secret_key


class Common(Configuration):
    VERSION = '0.4.0'
    API_VERSION = 'v1.3.0'

    SITE_ID = 1

    SECRET_KEY = get_secret_key()

    INSTALLED_APPS = [
        'django.contrib.sites',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'sortedm2m_filter_horizontal_widget',
        'oidc_provider',
        'rest_framework',
        'rest_framework.authtoken',
        'dj_rest_auth',
        'dj_rest_auth.registration',
        'multi_email_field',
        'kubeportal',    # positioned here to override allauth view templates
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'allauth.socialaccount.providers.google',
        'allauth.socialaccount.providers.oauth2',
        'silk',
        'django_extensions',
    ]

    MIDDLEWARE = [
        'silk.middleware.SilkyMiddleware',
        'kubeportal.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'kubeportal.middleware.HideAdminForNonStaffMiddleware'
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
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.template.context_processors.request',
                ],
            },
        },
    ]

    REST_FRAMEWORK = {
            'DEFAULT_VERSIONING_CLASS':
            'rest_framework.versioning.URLPathVersioning',
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
                ],
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticated',
                ],
            'DEFAULT_VERSION': API_VERSION,
            'ALLOWED_VERSIONS': [
                API_VERSION
                ]
            }

    REST_USE_JWT = True
    JWT_AUTH_COOKIE = 'kubeportal-auth'


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
        'django.contrib.auth.backends.ModelBackend',
        'kubeportal.ad.ActiveDirectoryBackend',
        'allauth.account.auth_backends.AuthenticationBackend'
    )

    SOCIALACCOUNT_QUERY_EMAIL = True
    SOCIALACCOUNT_PROVIDERS = {}
    AUTH_AD_DOMAIN = values.Value(None, environ_prefix='KUBEPORTAL')
    AUTH_AD_SERVER = values.Value(None, environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = values.Value(
        None, environ_name='AUTH_GOOGLE_KEY', environ_prefix='KUBEPORTAL')
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = values.Value(
        None, environ_name='AUTH_GOOGLE_SECRET', environ_prefix='KUBEPORTAL')
    if SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET:
        SOCIALACCOUNT_PROVIDERS['google'] = {
            'APP': {
                'secret': SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                'client_id': SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            },
            'SCOPE': ['profile', 'email'],
        }

    LOGIN_URL = '/'
    LOGIN_REDIRECT_URL = '/welcome/'
    LOGOUT_REDIRECT_URL = '/'
    STATIC_URL = '/static/'

    USE_I18N = True
    USE_L10N = True
    USE_TZ = True

    # Allow frontend dev server addresses as default, so that dev mode
    # works without an extra env variable being set
    ALLOWED_URLS = values.ListValue([], environ_prefix='KUBEPORTAL')
    ALLOWS_HOSTS = [urlparse(url).netloc for url in ALLOWED_URLS.value]

    AUTH_USER_MODEL = 'kubeportal.User'

    OIDC_TEMPLATES = {
        'authorize': 'oidc_authorize.html',
        'error': 'oidc_error.html'
    }
    OIDC_IDTOKEN_INCLUDE_CLAIMS = True  # include user email etc. in token
    SESSION_COOKIE_DOMAIN = values.Value(None, environ_prefix='KUBEPORTAL')
    NAMESPACE_CLUSTERROLES = values.ListValue([], environ_prefix='KUBEPORTAL')

    API_SERVER_EXTERNAL = values.Value(None, environ_prefix='KUBEPORTAL')

    BRANDING = values.Value('KubePortal', environ_prefix='KUBEPORTAL')
    LANGUAGE_CODE = values.Value('en-us', environ_prefix='KUBEPORTAL')
    TIME_ZONE = values.Value('UTC', environ_prefix='KUBEPORTAL')

    ADMIN_NAME = values.Value(environ_prefix='KUBEPORTAL')
    ADMIN_EMAIL = values.Value(environ_prefix='KUBEPORTAL')
    ADMINS = [(str(ADMIN_NAME), str(ADMIN_EMAIL)), ]

    OIDC_AFTER_USERLOGIN_HOOK = 'kubeportal.security.oidc_login_hook'

    ACCOUNT_ADAPTER = 'kubeportal.allauth.AccountAdapter'

    SILKY_AUTHENTICATION = True
    SILKY_AUTHORISATION = True

    LAST_LOGIN_MONTHS_AGO = values.Value(12, environ_prefix='KUBEPORTAL')

    # override default response format for /api/login endpoint
    REST_AUTH_SERIALIZERS = {
        'JWT_SERIALIZER': 'kubeportal.api.serializers.LoginSuccessSerializer'
    }


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
            'django': {
                'handlers': ['console', ],
                'level': 'INFO',
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

    EMAIL_HOST = values.Value('localhost', environ_prefix='KUBEPORTAL')

    LOG_LEVEL_PORTAL  = values.Value('ERROR', environ_prefix='KUBEPORTAL')
    LOG_LEVEL_REQUEST = values.Value('ERROR', environ_prefix='KUBEPORTAL')

    # read the environment variables immediately because they're used to
    # configure the loggers below
    LOG_LEVEL_PORTAL.setup('LOG_LEVEL_PORTAL')
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
        }
    }
