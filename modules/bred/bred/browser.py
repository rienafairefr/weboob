# -*- coding: utf-8 -*-

# Copyright(C) 2014 Romain Bignon
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

import json
from datetime import date
from decimal import Decimal

from weboob.capabilities.base import NotAvailable
from weboob.capabilities.bank import Account, Transaction
from weboob.exceptions import BrowserIncorrectPassword, BrowserHTTPError, BrowserUnavailable, ParseError
from weboob.browser import DomainBrowser


__all__ = ['BredBrowser']


class BredBrowser(DomainBrowser):
    BASEURL = 'https://www.bred.fr'

    def __init__(self, accnum, login, password, *args, **kwargs):
        super(BredBrowser, self).__init__(*args, **kwargs)
        self.login = login
        # Bred only use first 8 char (even if the password is set to be bigger)
        # The js login form remove after 8th char. No comment.
        self.password = password[:8]
        self.accnum = accnum
        self.universes = None
        self.current_univers = None

    def do_login(self, login, password):
        r = self.open('/transactionnel/Authentication', data={'identifiant': login, 'password': password})

        if 'gestion-des-erreurs/erreur-pwd' in r.url:
            raise BrowserIncorrectPassword('Bad login/password.')
        if 'gestion-des-erreurs/opposition' in r.url:
            raise BrowserIncorrectPassword('Your account is disabled')
        if '/pages-gestion-des-erreurs/erreur-technique' in r.url:
            raise BrowserUnavailable('A technical error occured')

    ACCOUNT_TYPES = {'000': Account.TYPE_CHECKING,
                     '999': Account.TYPE_MARKET,
                     '011': Account.TYPE_CARD,
                     '023': Account.TYPE_SAVINGS,
                     '078': Account.TYPE_SAVINGS,
                     '080': Account.TYPE_SAVINGS,
                     '027': Account.TYPE_SAVINGS,
                     '037': Account.TYPE_SAVINGS,
                     '730': Account.TYPE_DEPOSIT,
                    }

    def api_open(self, *args, **kwargs):
        try:
            return super(BredBrowser, self).open(*args, **kwargs)
        except BrowserHTTPError:
            self.do_login(self.login, self.password)
            return super(BredBrowser, self).open(*args, **kwargs)

    def set_universes(self):
        universes = []
        r = self.api_open('/transactionnel/services/applications/menu/getMenuUnivers')
        for univers in r.json()['content']['menus']:
            universes.append(univers['universKey'])
        if not universes:
            # There is just the default univers here.
            universes.append('')
            self.current_univers = ''
        else:
            # The following is needed to get the default univers in the list.
            self.move_to_univers(universes[0])
            r = self.api_open('/transactionnel/services/applications/menu/getMenuUnivers')
            for univers in r.json()['content']['menus']:
                if univers['universKey'] not in universes:
                    universes.append(univers['universKey'])
        self.universes = universes

    def move_to_univers(self, univers):
        x_token_bred = self.api_open('/transactionnel/services/rest/User/nonce?random=').json()['content']
        data = {}
        data['all'] = 'true'
        data['univers'] = univers
        self.api_open('/transactionnel/services/rest/User/switch', data=json.dumps(data), headers={'x-token-bred': x_token_bred})
        self.current_univers = univers

    def get_accounts_list(self):
        if not self.universes:
            self.set_universes()
        accounts = []
        for univers in self.universes:
            if univers != self.current_univers:
                self.move_to_univers(univers)
            accounts.extend(self.get_list())
        return accounts

    def get_list(self):
        r = self.api_open('/transactionnel/services/rest/Account/accounts')

        for content in r.json()['content']:
            if self.accnum != '00000000000' and content['numero'] != self.accnum:
                continue
            for poste in content['postes']:
                a = Account()
                a._number = content['numeroLong']
                iban_response = self.api_open('/transactionnel/services/rest/Account/account/%s/iban' % a._number).json()
                a.iban = iban_response['content']['iban'] if 'content' in iban_response else NotAvailable
                a._nature = poste['codeNature']
                a._consultable = poste['consultable']
                a._univers = self.current_univers
                a.id = '%s.%s' % (a._number, a._nature)
                a.type = self.ACCOUNT_TYPES.get(poste['codeNature'], Account.TYPE_UNKNOWN)

                if 'numeroDossier' in poste and poste['numeroDossier']:
                    a._file_number = poste['numeroDossier']
                    a.id += '.%s' % a._file_number

                if poste['postePortefeuille']:
                    a.label = u'Portefeuille Titres'
                    a.balance = Decimal(str(poste['montantTitres']['valeur']))
                    a.currency = poste['montantTitres']['monnaie']['code'].strip()
                    yield a

                if 'libelle' not in poste:
                    continue

                a.label = ' '.join([content['intitule'].strip(), poste['libelle'].strip()])
                a.balance = Decimal(str(poste['solde']['valeur']))
                a.currency = poste['solde']['monnaie']['code'].strip()
                yield a

    def get_history(self, account):
        if not account._consultable:
            raise NotImplementedError()

        if account._univers != self.current_univers:
            self.move_to_univers(account._univers)
        offset = 0
        next_page = True
        seen = set()
        while next_page:
            r = self.api_open('/transactionnel/services/applications/operations/get/%(number)s/%(nature)s/00/%(currency)s/%(startDate)s/%(endDate)s/%(offset)s/%(limit)s' %
                          {'number': account._number,
                           'nature': account._nature,
                           'currency': account.currency,
                           'startDate': '2000-01-01',
                           'endDate': date.today().strftime('%Y-%m-%d'),
                           'offset': offset,
                           'limit': 50
                          })
            next_page = False
            offset += 50
            transactions = []
            for op in reversed(r.json()['content']['operations']):
                next_page = True
                t = Transaction()
                if op['id'] in seen:
                    raise ParseError('There are several transactions with the same ID, probably an infinite loop')
                t.id = op['id']
                seen.add(t.id)
                t.amount = Decimal(str(op['montant']))
                t.date = date.fromtimestamp(op.get('dateDebit', op.get('dateOperation'))/1000)
                t.rdate = date.fromtimestamp(op.get('dateOperation', op.get('dateDebit'))/1000)
                t.vdate = date.fromtimestamp(op.get('dateValeur', op.get('dateDebit', op.get('dateOperation')))/1000)
                if 'categorie' in op:
                    t.category = op['categorie']
                t.label = op['libelle']
                t.raw = ' '.join([op['libelle']] + op['details'])
                transactions.append(t)

            # Transactions are unsorted
            for t in sorted(transactions, key=lambda t: t.rdate, reverse=True):
                yield t
