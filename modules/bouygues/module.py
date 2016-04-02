# -*- coding: utf-8 -*-

# Copyright(C) 2010-2015 Bezleputh
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


from weboob.capabilities.bill import CapDocument, Subscription, Document, SubscriptionNotFound, DocumentNotFound
from weboob.capabilities.messages import CantSendMessage, CapMessages, CapMessagesPost
from weboob.capabilities.base import find_object
from weboob.tools.backend import Module, BackendConfig
from weboob.tools.value import ValueBackendPassword, Value

from .browser import BouyguesBrowser


__all__ = ['BouyguesModule']


class BouyguesModule(Module, CapMessages, CapMessagesPost, CapDocument):
    NAME = 'bouygues'
    MAINTAINER = u'Bezleputh'
    EMAIL = 'carton_ben@yahoo.fr'
    VERSION = '1.2'
    DESCRIPTION = u'Bouygues Télécom French mobile phone provider'
    LICENSE = 'AGPLv3+'
    CONFIG = BackendConfig(Value('login', label='Login/Phone number'),
                           ValueBackendPassword('password', label='Password'))
    BROWSER = BouyguesBrowser

    def create_default_browser(self):
        return self.create_browser(self.config['login'].get(), self.config['password'].get())

    def post_message(self, message):
        if not message.content.strip():
            raise CantSendMessage(u'Message content is empty.')
        self.browser.post_message(message)

    def iter_subscription(self):
        return self.browser.get_subscription_list()

    def get_subscription(self, _id):
        return find_object(self.iter_subscription(), id=_id, error=SubscriptionNotFound)

    def get_document(self, _id):
        subid = _id.rsplit('_', 1)[0]
        subscription = self.get_subscription(subid)
        return find_object(self.iter_documents(subscription), id=_id, error=DocumentNotFound)

    def iter_documents(self, subscription):
        if not isinstance(subscription, Subscription):
            subscription = self.get_subscription(subscription)
        return self.browser.iter_documents(subscription)

    def download_document(self, document):
        if not isinstance(document, Document):
            document = self.get_document(document)
        return self.browser.open(document._url).content
