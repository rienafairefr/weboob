# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
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


import re
import urllib

from weboob.deprecated.browser import Browser, BrowserIncorrectPassword
from weboob.capabilities.bank import Account

from .pages import LoginPage, AccountsPage, ProAccountsPage, TransactionsPage, ProTransactionsPage, IbanPage, RedirectPage, AVPage


__all__ = ['CreditDuNordBrowser']


class CreditDuNordBrowser(Browser):
    PROTOCOL = 'https'
    ENCODING = 'UTF-8'
    PAGES = {'https://[^/]+/?':                                         LoginPage,
             'https://[^/]+/.*\?.*_pageLabel=page_erreur_connexion.*':  LoginPage,
             'https://[^/]+/swm/redirectCDN.html':                      RedirectPage,
             'https://[^/]+/vos-comptes/particuliers(\?.*)?':           AccountsPage,
             'https://[^/]+/vos-comptes/particuliers/transac_tableau_de_bord(\?.*)?':           AccountsPage,
             'https://[^/]+/vos-comptes/particuliers/V1_transactional_portal_page_.*':          AVPage,
             'https://[^/]+/vos-comptes/.*/transac/particuliers.*':     TransactionsPage,
             'https://[^/]+/vos-comptes/(?P<kind>professionnels|entreprises).*':    ProAccountsPage,
             'https://[^/]+/vos-comptes/.*/transac/(professionnels|entreprises).*': ProTransactionsPage,
             'https://[^/]+/vos-comptes/IPT/cdnProxyResource/transacClippe/RIB_impress.asp.*': IbanPage,
            }
    account_type = 'particuliers'

    def __init__(self, website, *args, **kwargs):
        self.DOMAIN = website
        Browser.__init__(self, *args, **kwargs)

    def is_logged(self):
        return self.page is not None and not self.is_on_page(LoginPage)

    def home(self):
        if self.is_logged():
            self.location(self.buildurl('/vos-comptes/%s' % self.account_type))
            self.location(self.page.document.xpath(u'//a[contains(text(), "Synthèse")]')[0].attrib['href'])
        else:
            self.login()

    def login(self):
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)

        self.location('https://' + self.DOMAIN, no_login=True)

        self.page.login(self.username, self.password)

        if not self.is_logged():
            raise BrowserIncorrectPassword()

        m = re.match('https://[^/]+/vos-comptes/(\w+).*', self.page.url)
        if m:
            self.account_type = m.group(1)

    def get_accounts_list(self, iban=True):
        if not self.is_on_page(AccountsPage):
            self.home()
        accounts = []
        self.location(self.page.get_av_link())
        if self.is_on_page(AVPage):
            for a in self.page.get_av_accounts():
                self.location(a._link, urllib.urlencode(a._args))
                self.location(a._link.replace("_attente", "_detail_contrat_rep"), urllib.urlencode(a._args))
                self.page.fill_valuation_diff(a)
                accounts.append(a)
        self.home()
        for a in self.page.get_list():
            accounts.append(a)
        if iban:
            self.page.iban_page()
            link = self.page.iban_go()
            for a in [a for a in accounts if a._acc_nb]:
                self.location('%s%s' % (link, a._acc_nb))
                a.iban = self.page.get_iban()
        return iter(accounts)

    def get_account(self, id):
        assert isinstance(id, basestring)

        l = self.get_accounts_list(iban=False)
        for a in l:
            if a.id == id:
                return a

        return None

    def iter_transactions(self, link, args, is_coming=None):
        if args is None:
            return

        while args is not None:
            self.location(link, urllib.urlencode(args))

            assert self.is_on_page(TransactionsPage)

            self.page.is_coming = is_coming

            for tr in self.page.get_history():
                yield tr

            is_coming = self.page.is_coming
            args = self.page.get_next_args(args)

    def get_history(self, account):
        for tr in self.iter_transactions(account._link, account._args):
            yield tr

        for tr in self.get_card_operations(account):
            yield tr

    def get_card_operations(self, account):
        for link_args in account._card_ids:
            for tr in self.iter_transactions(account._link, link_args, True):
                yield tr

    def get_investment(self, account):
        if not account._inv:
            return iter([])
        if (account.type == Account.TYPE_MARKET):
            self.location(account._link, urllib.urlencode(account._args))
            return self.page.get_market_investment()
        elif (account.type == Account.TYPE_LIFE_INSURANCE):
            self.location(account._link, urllib.urlencode(account._args))
            self.location(account._link.replace("_attente", "_detail_contrat_rep"), urllib.urlencode(account._args))
            return self.page.get_deposit_investment()
        return iter([])
