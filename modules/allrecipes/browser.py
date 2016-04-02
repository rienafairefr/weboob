# -*- coding: utf-8 -*-

# Copyright(C) 2013 Julien Veyssier
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
from weboob.browser import PagesBrowser, URL
from .pages import ResultsPage, RecipePage, HomePage

import urllib

__all__ = ['AllrecipesBrowser']


class AllrecipesBrowser(PagesBrowser):
    BASEURL = 'https://apps.allrecipes.com'
    results = URL('/v1/recipes\?(?P<query>.*)', ResultsPage)
    recipe = URL('/v1/recipes/(?P<_id>.*)/', RecipePage)
    home = URL('http://allrecipes.com', HomePage)

    TOKEN = None

    def fill_token(self):
        self.home.open()
        self.TOKEN = 'Bearer %s' % self.session.cookies.get('ARToken')
        self.session.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.session.headers['Authorization'] = self.TOKEN

    def iter_recipes(self, pattern):
        query = {'query': pattern,
                 'page': 1,
                 'pagesize': 20,
                 'sort': 're'}

        if not self.TOKEN:
            self.fill_token()

        return self.results.go(query=urllib.urlencode(query)).iter_recipes()

    def get_recipe(self, _id, obj=None):
        if not self.TOKEN:
            self.fill_token()

        recipe = self.recipe.go(_id=_id).get_recipe(obj=obj)
        comments = list(self.page.get_comments())
        if comments:
            recipe.comments = comments
        return recipe
