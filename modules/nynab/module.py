from weboob.tools.backend import Module, BackendConfig
from weboob.tools.value import Value, ValueBackendPassword

__all__ = ['nYNABmodule']


class nYNABmodule(Module):
    NAME = 'nynab'
    CONFIG = BackendConfig(Value('login', label='Email'),
                                   ValueBackendPassword('password', label='Password'),
                           Value('budgetname',label='Budget Name'))
    LICENSE = 'AGPLv3+'
    VERSION = '1.2'
    MAINTAINER = 'rienafairefr'
    EMAIL = 'rienafairefr@gmail.com'
    DESCRIPTION = 'Backend to send boobank transactions to nYNNAB www.youneedabudget.com'
