import pytest
import functools
import mockldap
from mock import patch
from adreset2.utils import *


def manage_mock_ldap(f):
    """ Decorates test functions to start and stop the mocked LDAP directory
    """
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        # Creates the MockLdap instance with our directory defined in the class
        self.mock_ldap_obj = mockldap.MockLdap(self.directory)
        self.mock_ldap_obj.start()

        # Runs the decorated function
        rv = f(self, *args, **kwargs)

        # Cleans up the mock LDAP directory
        self.mock_ldap_obj.stop()
        return rv
    return wrapped


class Test_AD_Class:

    domain = (
        'DC=example,DC=local', {
            'objectClass': ['top', 'domain', 'domainDNS'],
            'name': ['example'],
            'distinguishedName': ['DC=example,DC=local'],
            # Using a hex SID because the AD class converts the returned hex SID to a string format
            'objectSid':
                ['\x01\x04\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00=\x12\xb7KE\xa7\x8d\xe2wZ\xff\xb3']
        }
    )

    domain_users_group = (
        'CN=Domain Users,CN=Users,DC=example,DC=local', {
            'objectClass': ['top', 'group'],
            'distinguishedName': ['CN=Domain Users,CN=Users,DC=example,DC=local'],
            'sAMAccountName': ['Domain Users'],
            # Using a human readable SID because AD can be queried for hex or human readable
            # the AD class will be querying by the human readable format
            'objectSid': ['S-1-5-21-1270288957-3800934213-3019856503-513']
        }
    )

    adreset_admins_group = (
        'CN=ADReset Admins,OU=Groups,DC=example,DC=local', {
            'objectClass': ['top', 'group'],
            'distinguishedName': ['CN=ADReset Admins,OU=Groups,DC=example,DC=local'],
            'sAMAccountName': ['ADReset Admins'],
            # Using a human readable SID because AD can be queried for hex or human readable
            # the AD class will be querying by the human readable format
            'objectSid': ['S-1-5-21-1270288957-3800934213-3019856503-1105']
        }
    )

    # A test user that is authorized to administer ADReset based on group membership
    svc_account = (
        'CN=svcADReset,CN=Users,DC=example,DC=local', {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'distinguishedName': ['CN=svcADReset,CN=Users,DC=example,DC=local'],
            'sAMAccountName': ['svcADReset'],
            'userPrincipalName': ['svcADReset@example.local'],
            'displayName': ['ADReset Service Account'],
            'name': ['svcADReset'],
            # Although AD uses unicodePwd for its password, MockLDAP only supports userPassword for logins
            'userPassword': ['P@ssW0rd'],
            'primaryGroupID': ['513'],
            'memberOf': ['CN=Some Group,OU=Groups,DC=example,DC=local',
                         'CN=Dome Group 2,OU=Groups,DC=example,DC=local']
        }
    )

    directory = dict([domain, domain_users_group, adreset_admins_group, svc_account])
    mock_ldap_obj = None
    ad_obj = None

    @manage_mock_ldap
    def test_try_ad_connection(self):
        result = try_ad_connection('example.local', 636, 'example.local',
                                   'CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd')
        assert result is True

    @manage_mock_ldap
    def test_ad_init(self):
        ad_obj = AD()
        assert isinstance(ad_obj.ldap_connection, mockldap.ldapobject.LDAPObject) is True

    @manage_mock_ldap
    def test_login(self):
        ad_obj = AD()
        result = ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd')
        assert result is True

    @manage_mock_ldap
    def test_login_bad_password(self):
        ad_obj = AD()
        with pytest.raises(ADException) as excinfo:
            ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'WrongP@ssW0rd')
        assert excinfo.value.message == 'The username or password was incorrect'

    @manage_mock_ldap
    def test_svc_account_login(self):
        ad_obj = AD()
        ad_obj.svc_account_login()
        assert ad_obj.ldap_connection.whoami_s() == 'dn:CN=svcADReset,CN=Users,DC=example,DC=local'

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\svcADReset')
    @manage_mock_ldap
    def test_get_loggedin_user(self, mock_whoami_s):
        ad_obj = AD()
        login_result = ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd')
        assert login_result is True
        assert ad_obj.get_loggedin_user() == 'svcADReset'


    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\svcADReset')
    @manage_mock_ldap
    def test_get_loggedin_user_display_name(self, mock_whoami_s):
        ad_obj = AD()
        login_result = ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd')
        assert login_result is True
        assert ad_obj.get_loggedin_user_display_name() == 'ADReset Service Account'
