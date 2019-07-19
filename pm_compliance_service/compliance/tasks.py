from typing import Dict, List, NoReturn

from celery import app
from celery.utils.log import get_task_logger
from django.conf import settings
from redis.exceptions import LockError

from .clients import get_aml_client
from .exceptions import FailedRequestException
from .repositories.redis_repository import RedisRepository


logger = get_task_logger(__name__)


# Lock timeout of 2 minutes (just in the case that the application hangs to avoid a redis deadlock)
LOCK_TIMEOUT = 60 * 2


# https://docs.celeryproject.org/en/latest/userguide/tasks.html#using-a-custom-retry-delay
@app.shared_task(bind=True,
                 soft_time_limit=settings.DEFAULT_TASK_SOFT_TIME_LIMIT,
                 max_retries=settings.DEFAULT_TASK_RETRIES)
def aml_prescreening_task(self, address: str, asset: str, user_id: str, retry: bool = True) -> NoReturn:
    """
    Executes the pre-screening.
    :return: None
    """
    try:
        redis = RedisRepository().redis

        with redis.lock(f'tasks:aml_prescreening_task-{address}', blocking_timeout=1, timeout=LOCK_TIMEOUT):
            client = get_aml_client()
            try:
                results: List = client.post_prescreening(address, asset, user_id)
                # TODO process result data and integrate with other AML services.
            except FailedRequestException as exc:
                if retry:
                    raise self.retry(countdown=settings.DEFAULT_TASK_DELAY)
                else:
                    raise exc
    except LockError:
        logger.info(f'aml_prescreening_task-{address} is locked')
