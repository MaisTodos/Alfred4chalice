import json
import uuid
from unittest.mock import patch

from botocore.exceptions import ClientError

from alfred.settings import SQS_QUEUE_URL
from alfred.sqs.exceptions import SQSTaskError, SQSTaskMaxRetriesExceededError
from alfred.sqs.handlers import SQSHandler
from alfred.sqs.models import DeadTask
from alfred.sqs.sqs import SQSTask
from tests.tools import sqs_expected_params


def test_sqs_task_error():
    assert issubclass(SQSTaskError, Exception) is True


def test_sqs_task_max_retries_exceeded_error():
    assert issubclass(SQSTaskMaxRetriesExceededError, Exception) is True


def test_sqs_task_queue_url_property():
    assert SQSTask.default_queue_url == SQS_QUEUE_URL


def test_sqs_task_default_delay_property():
    assert SQSTask.default_delay == 1


def test_sqs_task_max_retries_property():
    assert SQSTask.max_retries == 3


def test_sqs_task_default_retry_delay_property():
    assert SQSTask.default_retry_delay == 60 * 3


@SQSTask(bind=True)
def foo(self, param_a, param_b):
    return "bar"


@SQSTask()
def foobar(param_a, param_b):
    return "bar"


@SQSTask(queue_url="fake_url.fifo", message_group_id="fake_message_group_id")
def fifo_example(param_a, param_b):
    return "bar"


def test_sqs_task_init():
    assert foo.bind is True
    assert foo.retries == 0


def test_sqs_task_apply():
    response = foobar.apply(args=["fubar"], kwargs={"param_b": 10})
    assert response == "bar"


@patch("alfred.sqs.sqs.sentry_sdk")
@patch("alfred.sqs.sqs.sqs_client")
def test_apply_side_effect_async(mock_sqs_client, mock_sentry):
    mock_sqs_client.send_message.side_effect = ClientError(
        error_response={}, operation_name=""
    )
    foo.apply_async(args=["fubar"], kwargs={"param_b": 10})
    mock_sentry.capture_message.assert_called_once()


@patch("alfred.sqs.sqs.sqs_client")
def test_apply_async(mock_sqs_client):
    response = foo.apply_async(args=["fubar"], kwargs={"param_b": 10})

    mock_sqs_client.send_message.assert_called_once_with(
        QueueUrl=foo.queue_url,
        DelaySeconds=foo.default_delay,
        MessageBody=json.dumps(
            {
                "_func_module": foo.func.__module__,
                "_func_name": foo.func.__name__,
                "args": ["fubar"],
                "kwargs": {"param_b": 10},
                "retries": 0,
            }
        ),
    )
    assert response == mock_sqs_client.send_message.return_value["MessageId"]


@patch("alfred.sqs.sqs.sqs_client")
def test_apply_async_with_countdown(mock_sqs_client):
    response = foo.apply_async(
        args=["fubar"],
        kwargs={"param_b": 10},
        countdown=30,
    )

    mock_sqs_client.send_message.assert_called_once_with(
        QueueUrl=foo.queue_url,
        DelaySeconds=30,
        MessageBody=json.dumps(
            {
                "_func_module": foo.func.__module__,
                "_func_name": foo.func.__name__,
                "args": ["fubar"],
                "kwargs": {"param_b": 10},
                "retries": 0,
            }
        ),
    )
    assert response == mock_sqs_client.send_message.return_value["MessageId"]


@patch("alfred.sqs.sqs.sqs_client")
def test_apply_async_with_queue_url(mock_sqs_client):
    response = foo.apply_async(
        args=["fubar"],
        kwargs={"param_b": 10},
        queue_url="fake-queue",
    )

    mock_sqs_client.send_message.assert_called_once_with(
        QueueUrl="fake-queue",
        DelaySeconds=foo.default_delay,
        MessageBody=json.dumps(
            {
                "_func_module": foo.func.__module__,
                "_func_name": foo.func.__name__,
                "args": ["fubar"],
                "kwargs": {"param_b": 10},
                "retries": 0,
            }
        ),
    )
    assert response == mock_sqs_client.send_message.return_value["MessageId"]


@patch("alfred.sqs.sqs.sqs_client")
def test_apply_async_with_message_group_id(mock_sqs_client):
    response = fifo_example.apply_async(args=["fubar"], kwargs={"param_b": 10})

    mock_sqs_client.send_message.assert_called_once_with(
        QueueUrl=fifo_example.queue_url,
        MessageBody=json.dumps(
            {
                "_func_module": fifo_example.func.__module__,
                "_func_name": fifo_example.func.__name__,
                "args": ["fubar"],
                "kwargs": {"param_b": 10},
                "retries": 0,
            }
        ),
        MessageGroupId="fake_message_group_id",
    )
    assert response == mock_sqs_client.send_message.return_value["MessageId"]


def test_sqs_handler_init():
    body = {"foo": "bar"}
    handler = SQSHandler(json.dumps(body))

    assert handler.body == body
    assert handler.aws_request_id is None
    assert handler.message_id is None


def test_sqs_handler_init_with_request_and_message_id():
    body = {"foo": "bar"}
    aws_request_id = "fake_aws_request_id"
    message_id = "fake_message_id"

    handler = SQSHandler(json.dumps(body), aws_request_id, message_id)

    assert handler.body == body
    assert handler.aws_request_id == aws_request_id
    assert handler.message_id == message_id


def test_sqs_handler_apply():
    body = {
        "_func_module": foo.func.__module__,
        "_func_name": foo.func.__name__,
        "args": ["fubar"],
        "kwargs": {"param_b": 10},
        "retries": 1,
    }
    handler = SQSHandler(json.dumps(body))
    response = handler.apply()

    assert response == "bar"


@patch("alfred.sqs.handlers.sqs_client")
def test_sqs_handler_sqs_delete_message(mock_sqs_client):
    body = {"foo": "bar"}
    handler = SQSHandler(json.dumps(body))
    handler.sqs_delete_message("fake-queue", "fake-receipt-handle")

    mock_sqs_client.delete_message.assert_called_once_with(
        QueueUrl="fake-queue", ReceiptHandle="fake-receipt-handle"
    )


@SQSTask(bind=True)
def foo_with_retry(self, param_a, param_b):
    try:
        resp = 10 + "bar"
    except TypeError as err:
        return self.retry(err=err, max_retries=3, countdown=500)
    return resp


def test_sqs_task_retry(sqs_stub):
    expected_params_send_sms = sqs_expected_params(
        foo_with_retry,
        task_args=["fubar"],
        task_kwargs={"param_b": 10},
        task_countdown=500,
        task_retries=1,
    )
    sqs_stub.add_response(
        "send_message",
        service_response={"MessageId": str(uuid.uuid4())},
        expected_params=expected_params_send_sms,
    )
    body = {
        "_func_module": foo_with_retry.func.__module__,
        "_func_name": foo_with_retry.func.__name__,
        "args": ["fubar"],
        "kwargs": {"param_b": 10},
        "retries": 0,
    }

    handler = SQSHandler(json.dumps(body))
    response = handler.apply()

    assert response is None


@patch("alfred.sqs.sqs.logger.error")
def test_sqs_task_retry_raise_max_retries_exceeded(mock_logger, sqs_stub):
    body = {
        "_func_module": foo_with_retry.func.__module__,
        "_func_name": foo_with_retry.func.__name__,
        "args": ["fubar"],
        "kwargs": {"param_b": 10},
        "retries": 2,
    }

    handler = SQSHandler(json.dumps(body))
    handler.apply()

    mock_logger.assert_called_once_with(
        {
            "task_has_succeeded": False,
            "task_error_message": "Task achieve the max retries possible: 3",
            "task_function_module": body["_func_module"],
            "task_function_name": body["_func_name"],
            "task_function_args": body["args"],
            "task_function_kwargs": body["kwargs"],
            "task_function_retries": body["retries"] + 1,
            "task_queue_url": "",
            "task_response": None,
        }
    )


@SQSTask(bind=True, dead_retry=True)
def foo_with_dead_retry(self, param_a, param_b):
    try:
        resp = 10 + "bar"
    except TypeError as err:
        return self.retry(err=err, max_retries=3, countdown=500)
    return resp


@patch("alfred.sqs.sqs.logger.error")
def test_sqs_task_with_flag_dead_retry(mock_logger, sqs_stub, dynamo_setup):
    body = {
        "_func_module": foo_with_dead_retry.func.__module__,
        "_func_name": foo_with_dead_retry.func.__name__,
        "args": ["fubar"],
        "kwargs": {"param_b": 10},
        "retries": 2,
    }

    handler = SQSHandler(json.dumps(body))
    handler.apply()

    mock_logger.assert_called_once_with(
        {
            "task_has_succeeded": False,
            "task_error_message": "Task achieve the max retries possible: 3",
            "task_function_module": body["_func_module"],
            "task_function_name": body["_func_name"],
            "task_function_args": body["args"],
            "task_function_kwargs": body["kwargs"],
            "task_function_retries": body["retries"] + 1,
            "task_queue_url": "",
            "task_response": None,
        }
    )

    dead_task = DeadTask.scan().__next__()

    assert dead_task.function_module == body["_func_module"]
    assert dead_task.function_name == body["_func_name"]
    assert dead_task.function_args == body["args"]
    assert dead_task.function_kwargs == body["kwargs"]
    assert dead_task.function_retries == body["retries"] + 1
    assert dead_task.queue_url == ""


def test_sqs_send_dead_task(dynamo_setup):
    body = {
        "_func_module": foo_with_dead_retry.func.__module__,
        "_func_name": foo_with_dead_retry.func.__name__,
        "args": ["fubar"],
        "kwargs": {"param_b": 10},
        "retries": 2,
    }

    handler = SQSHandler(json.dumps(body))
    handler.apply()

    dead_task = DeadTask.scan().__next__()

    dead_task.run()


@SQSTask(bind=True, once_time=60)
def foo_return_bar(self, *args, **kwargs):
    return "bar"


@patch("alfred.cache.walrus_cache.Cache.get")
@patch("alfred.cache.walrus_cache.Cache.set")
def test_check_sqs_with_cache(mock_cache_set, mock_cache_get):
    mock_cache_get.return_value = True

    foo_return_bar.apply(args=["foobar"], kwargs={"param_b": 10})

    mock_cache_set.assert_not_called()


@patch("alfred.cache.walrus_cache.Cache.get")
@patch("alfred.cache.walrus_cache.Cache.set")
def test_check_sqs_without_cache(mock_cache_set, mock_cache_get):
    mock_cache_get.return_value = False

    foo_return_bar.apply(args=["foobar"], kwargs={"param_b": 10})

    mock_cache_set.assert_called_once()


@SQSTask(bind=True, fail_silently=True)
def foo_silently(self, param_a, param_b):
    try:
        resp = 10 + "bar"
    except TypeError as err:
        return self.retry(err=err, max_retries=3, countdown=500)
    return resp


@patch("alfred.sqs.sqs.logger.info")
def test_sqs_task_retry_raise_max_retries_exceeded_with_fail_silently(
    mock_logger, sqs_stub
):
    body = {
        "_func_module": foo_silently.func.__module__,
        "_func_name": foo_silently.func.__name__,
        "args": ["fubar"],
        "kwargs": {"param_b": 10},
        "retries": 2,
    }
    handler = SQSHandler(json.dumps(body))
    handler.apply()

    mock_logger.assert_called_once_with(
        {
            "task_has_succeeded": False,
            "task_error_message": "Task achieve the max retries possible: 3",
            "task_function_module": body["_func_module"],
            "task_function_name": body["_func_name"],
            "task_function_args": body["args"],
            "task_function_kwargs": body["kwargs"],
            "task_function_retries": body["retries"] + 1,
            "task_queue_url": "",
            "task_response": None,
        }
    )
