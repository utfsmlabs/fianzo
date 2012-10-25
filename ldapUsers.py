# Copyright (C) 2012 Universidad Tecnica Federico Santa Maria
#
# This file is part of Fianzo.
#
# Fianzo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fianzo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fianzo.  If not, see <http://www.gnu.org/licenses/>.

import ldap

class ldapConnection:
    def __init__(self, app):
        self.app = app
        
        self.uri = app.config['LDAP_URI']
        self.searchAttribute = app.config['LDAP_SEARCH_ATTR']
        self.baseDN = app.config['LDAP_BASEDN']

    def search(self, attr):
        searchFilter = '(%s=%s)' % (self.searchAttribute, attr)

        conn = ldap.initialize(self.uri)
        conn.simple_bind_s()
        results = conn.search_ext_s(
                self.baseDN, ldap.SCOPE_SUBTREE, searchFilter)
        conn.unbind_s()

        return results

    def getDN(self, attr):
        result = self.search(attr)
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        else:
            return None

    def search_and_auth(self, attr, passwd):
        dn = self.getDN(attr)
        
        conn = ldap.initialize(self.uri)
        try:
            conn.simple_bind_s(dn, passwd)
            return True
        except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM):
            return False


def extractNamingAttribute(dn):
    return dn.split(',')[0].split('=')[-1]

