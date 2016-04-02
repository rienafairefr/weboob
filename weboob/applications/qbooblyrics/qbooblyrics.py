# -*- coding: utf-8 -*-

# Copyright(C) 2016 Julien Veyssier
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


from weboob.capabilities.lyrics import CapLyrics
from weboob.tools.application.qt5 import QtApplication

from .main_window import MainWindow


class QBooblyrics(QtApplication):
    APPNAME = 'qbooblyrics'
    VERSION = '1.2'
    COPYRIGHT = 'Copyright(C) 2016 Julien Veyssier'
    DESCRIPTION = "Qt application allowing to search song lyrics."
    SHORT_DESCRIPTION = "search lyrics"
    CAPS = CapLyrics
    CONFIG = {'settings': {'backend': '',
                           'maxresultsnumber': '10'
                           }
              }

    def main(self, argv):
        self.load_backends([CapLyrics])
        self.load_config()

        self.main_window = MainWindow(self.config, self.weboob, self)
        self.main_window.show()
        return self.weboob.loop()
