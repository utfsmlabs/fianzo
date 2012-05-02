import ldap

class ldapConnection:
    def __init__(self, app):
        self.app = app
        
        self.uri = app.config['LDAP_URI']
        self.searchAttribute = app.config['LDAP_SEARCH_ATTR']
        self.baseDN = app.config['LDAP_BASEDN']

    def search(self, attr):
        searchFilter = '(%s=%s)' % (self.searchAttribute, attr)
        print searchFilter

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

def extractNamingAttribute(dn):
    return dn.split(',')[0].split('=')[-1]
