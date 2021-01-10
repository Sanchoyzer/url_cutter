class BaseExc(Exception):
    pass


class ServerError(BaseExc):
    pass


class ClientError(BaseExc):
    pass


class AuthError(ClientError):
    pass


class UidAlreadyInUse(ClientError):
    pass


class UrlNotAvailable(ClientError):
    pass


class UrlAlreadyShort(ClientError):
    pass
