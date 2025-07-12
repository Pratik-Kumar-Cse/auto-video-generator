import sentry_sdk
from app.core.config import settings


class SentryClient(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SentryClient, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            default_integrations=False,
            include_source_context=False,
            include_local_variables=False,
            max_request_body_size="never",
            profiles_sample_rate=1.0,
            traces_sample_rate=1.0,
        )

    def capture_exception(self, e, tags={}):
        with sentry_sdk.push_scope() as scope:
            for key, value in tags.items():
                scope.set_tag(key, value)
            sentry_sdk.capture_exception(e)


sentry_client = SentryClient()
