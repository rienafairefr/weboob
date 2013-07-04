# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Bezleputh
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

from weboob.capabilities.job import BaseJobAdvert


class AdeccoJobAdvert(BaseJobAdvert):
    @classmethod
    def id2url(cls, _id):
        splitted_id = _id.split('/')
        return 'http://www.adecco.fr/trouver-un-emploi/Pages/Details-de-l-Offre/%s/%s.aspx?IOF=%s' % (splitted_id[0], splitted_id[1], splitted_id[2])