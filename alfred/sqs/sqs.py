import json
import logging
from hashlib import md5

from botocore.exceptions import ClientError

from alfred.cache.walrus_cache import Cache
from alfred.sentry import sentry_sdk
from alfred.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, SQS_QUEUE_URL
from alfred.sqs.models import DeadTask

from . import sqs_client

logger = logging.getLogger("base")


DEFAULT_QUEUE_URL = SQS_QUEUE_URL
DEFAULT_DELAY = 1
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 60 * 3


class SQSTask:
    default_queue_url = DEFAULT_QUEUE_URL
    default_delay = DEFAULT_DELAY
    max_retries = DEFAULT_MAX_RETRIES
    default_retry_delay = DEFAULT_RETRY_DELAY

    def __init__(
        self,
        bind=False,
        retries=0,
        queue_url=None,
        dead_retry=False,
        once_time=None,
        fail_silently=False,
        message_group_id=None,
    ):
        self.dead_retry = dead_retry
        self.retries = retries
        self.bind = bind
        self.queue_url = queue_url or DEFAULT_QUEUE_URL
        self.once_time = once_time
        self.fail_silently = fail_silently
        self.message_group_id = message_group_id

    def __call__(self, func):
        self.func = func
        return self

    def apply_async(self, args=[], kwargs={}, queue_url=None, countdown=default_delay):
        body = {
            "_func_module": self.func.__module__,
            "_func_name": self.func.__name__,
            "args": args,
            "kwargs": kwargs,
            "retries": self.retries,
        }

        message_params = {
            "QueueUrl": queue_url or self.queue_url,
            "MessageBody": json.dumps(body),
        }

        if not self.message_group_id:
            message_params["DelaySeconds"] = countdown  # Default Queue
        else:
            message_params["MessageGroupId"] = self.message_group_id  # FIFO

        try:
            response = sqs_client.send_message(**message_params)
            return response["MessageId"]
        except ClientError as err:
            data_exception = {
                "err": str(err),
                "queue_url": queue_url,
                "response": err.response
            }
            sentry_sdk.capture_message(str(data_exception))

    def apply(self, args=[], kwargs={}):
        if self._assert_once_apply(args, kwargs):
            return None
        return self._run(0, *args, **kwargs)

    def _assert_once_apply(self, args=[], kwargs={}):
        if self.once_time:
            cache_key = f"{self.func.__module__}.{self.func.__name__}:{args}_{kwargs}"
            hash_key = md5(cache_key.encode()).hexdigest()

            cache = Cache()
            cached = cache.get(hash_key)

            if cached:
                return True

            cache.set(hash_key, cache_key, self.once_time)
            return False

    def _save_request(self, *args, **kwargs):
        self.request_args = [*args]
        self.request_kwargs = kwargs

    def _run(self, retries, *args, **kwargs):
        self.retries = retries
        self._save_request(*args, **kwargs)

        if self.bind:
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)

    def retry(
        self,
        err,
        *args,
        max_retries=DEFAULT_MAX_RETRIES,
        countdown=DEFAULT_RETRY_DELAY,
        queue_url=None,
        **kwargs,
    ):
        self.retries += 1

        if self.retries >= max_retries:
            log_function = logger.info if self.fail_silently else logger.error
            log_function(
                {
                    "task_has_succeeded": False,
                    "task_error_message": f"Task achieve the max retries possible: {max_retries}",  # noqa: E501
                    "task_function_module": self.func.__module__,
                    "task_function_name": self.func.__name__,
                    "task_function_args": self.request_args,
                    "task_function_kwargs": self.request_kwargs,
                    "task_function_retries": self.retries,
                    "task_queue_url": self.queue_url,
                    "task_response": None,
                }
            )

            if self.dead_retry:
                DeadTask(
                    function_module=self.func.__module__,
                    function_name=self.func.__name__,
                    function_args=self.request_args,
                    function_kwargs=self.request_kwargs,
                    function_retries=self.retries,
                    queue_url=self.queue_url,
                ).save()

            return None

        queue_url = queue_url or self.queue_url
        self.apply_async(
            args=self.request_args,
            kwargs=self.request_kwargs,
            queue_url=queue_url,
            countdown=countdown,
        )
        return
