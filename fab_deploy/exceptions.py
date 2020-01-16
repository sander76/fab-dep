import logging

_LOGGER = logging.getLogger(__name__)


class EchoException(Exception):
    pass


class FatalEchoException(Exception):
    pass
