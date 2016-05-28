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
        self.ad_obj = AD()

        # Runs the decorated function
        rv = f(self, *args, **kwargs)

        self.ad_obj = None
        # Cleans up the mock LDAP directory
        self.mock_ldap_obj.stop()
        return rv
    return wrapped


def mocked_nested_group_members_query():
    """ Returns mocked output of the memberOf:1.2.840.113556.1.4.1941 LDAP query
    """
    return [('CN=user1,CN=Users,DC=example,DC=local', {}),
            ('CN=user16,CN=Users,DC=example,DC=local', {}),
            (None, ['ldaps://ForestDnsZones.example.local/DC=ForestDnsZones,DC=example,DC=local']),
            (None, ['ldaps://DomainDnsZones.example.local/DC=DomainDnsZones,DC=example,DC=local']),
            (None, ['ldaps://example.local/CN=Configuration,DC=example,DC=local'])]


class Test_AD_Class:

    domain = (
        'DC=example,DC=local', {
            'objectClass': ['top', 'domain', 'domainDNS'],
            'name': ['example'],
            'distinguishedName': ['DC=example,DC=local'],
            'minPwdLength': ['7'],
            'pwdProperties': ['1'],
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

    svc_account = (
        'CN=svcADReset,CN=Users,DC=example,DC=local', {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'distinguishedName': ['CN=svcADReset,CN=Users,DC=example,DC=local'],
            'sAMAccountName': ['svcADReset'],
            'userPrincipalName': ['svcADReset@example.local'],
            'displayName': ['ADReset Service Account'],
            'name': ['svcADReset'],
            'mail': ['svcADReset@example.local'],
            'lockoutTime': ['0'],
            'userAccountControl': ['512'],
            'unicodePwd': ['P@ssW0rd'],
            # Although AD uses unicodePwd for its password, MockLDAP only supports userPassword for logins
            'userPassword': ['P@ssW0rd'],
            'primaryGroupID': ['513'],
            'memberOf': ['CN=Some Group,OU=Groups,DC=example,DC=local',
                         'CN=Some Group 2,OU=Groups,DC=example,DC=local']
        }
    )

    user1 = (
        'CN=user1,CN=Users,DC=example,DC=local', {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'distinguishedName': ['CN=user1,CN=Users,DC=example,DC=local'],
            'sAMAccountName': ['user1'],
            'userPrincipalName': ['user1@example.local'],
            'displayName': ['Some User'],
            'name': ['user1'],
            'mail': ['user1@example.local'],
            'lockoutTime': ['0'],
            'userAccountControl': ['512'],
            'unicodePwd': ['P@ssW0rd'],
            # Although AD uses unicodePwd for its password, MockLDAP only supports userPassword for logins
            'userPassword': ['P@ssW0rd'],
            'primaryGroupID': ['513'],
            'memberOf': ['CN=ADReset Admins,OU=Groups,DC=example,DC=local',
                         'CN=Some Group 2,OU=Groups,DC=example,DC=local']
        }
    )

    user2 = (
        'CN=user2,CN=Users,DC=example,DC=local', {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'distinguishedName': ['CN=user2,CN=Users,DC=example,DC=local'],
            'sAMAccountName': ['user2'],
            'userPrincipalName': ['user2@example.local'],
            'displayName': ['Some User'],
            'name': ['user2'],
            'mail': ['user2@example.local'],
            'lockoutTime': ['0'],
            'userAccountControl': ['512'],
            'unicodePwd': ['P@ssW0rd'],
            # Although AD uses unicodePwd for its password, MockLDAP only supports userPassword for logins
            'userPassword': ['P@ssW0rd'],
            'primaryGroupID': ['1105'],
            'memberOf': ['CN=Some Group,OU=Groups,DC=example,DC=local',
                         'CN=Some Group 2,OU=Groups,DC=example,DC=local']
        }
    )

    locked_user = (
        'CN=locked_user,CN=Users,DC=example,DC=local', {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'distinguishedName': ['CN=locked_user,CN=Users,DC=example,DC=local'],
            'sAMAccountName': ['locked_user'],
            'userPrincipalName': ['locked_user@example.local'],
            'displayName': ['Locked User'],
            'name': ['locked_user'],
            'mail': ['locked_user@example.local'],
            'lockoutTime': ['166446620723456785'],
            'userAccountControl': ['512'],
            'unicodePwd': ['P@ssW0rd'],
            # Although AD uses unicodePwd for its password, MockLDAP only supports userPassword for logins
            'userPassword': ['P@ssW0rd'],
            'primaryGroupID': ['513'],
            'memberOf': ['CN=ADReset Admins,OU=Groups,DC=example,DC=local',
                         'CN=Some Group 2,OU=Groups,DC=example,DC=local']
        }
    )

    disabled_user = (
        'CN=disabled_user,CN=Users,DC=example,DC=local', {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'distinguishedName': ['CN=disabled_user,CN=Users,DC=example,DC=local'],
            'sAMAccountName': ['disabled_user'],
            'userPrincipalName': ['disabled_user@example.local'],
            'displayName': ['Disabled User'],
            'name': ['disabled_user'],
            'mail': ['disabled_user@example.local'],
            'lockoutTime': ['0'],
            'userAccountControl': ['514'],
            'unicodePwd': ['P@ssW0rd'],
            # Although AD uses unicodePwd for its password, MockLDAP only supports userPassword for logins
            'userPassword': ['P@ssW0rd'],
            'primaryGroupID': ['513'],
            'memberOf': ['CN=ADReset Admins,OU=Groups,DC=example,DC=local',
                         'CN=Some Group 2,OU=Groups,DC=example,DC=local']
        }
    )

    directory = dict([domain, domain_users_group, adreset_admins_group,
                      svc_account, user1, user2, locked_user, disabled_user])
    mock_ldap_obj = None
    ad_obj = None

    @manage_mock_ldap
    def test_try_ad_connection(self):
        result = try_ad_connection('example.local', 636, 'example.local',
                                   'CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd')
        assert result is True

    @manage_mock_ldap
    def test_ad_init(self):
        assert isinstance(self.ad_obj.ldap_connection, mockldap.ldapobject.LDAPObject) is True

    @manage_mock_ldap
    def test_login(self):
        result = self.ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd')
        assert result is True

    @manage_mock_ldap
    def test_login_bad_password(self):
        with pytest.raises(ADException) as excinfo:
            self.ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'WrongP@ssW0rd')
        assert excinfo.value.message == 'The username or password was incorrect'

    @manage_mock_ldap
    def test_svc_account_login(self):
        self.ad_obj.svc_account_login()
        assert self.ad_obj.ldap_connection.whoami_s() == 'dn:CN=svcADReset,CN=Users,DC=example,DC=local'

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\svcADReset')
    @manage_mock_ldap
    def test_get_loggedin_user(self, mock_whoami_s):
        assert self.ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd') is True
        assert self.ad_obj.get_loggedin_user() == 'svcADReset'

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\svcADReset')
    @manage_mock_ldap
    def test_get_loggedin_user_display_name(self, mock_whoami_s):
        ad_obj = AD()
        assert ad_obj.login('CN=svcADReset,CN=Users,DC=example,DC=local', 'P@ssW0rd') is True
        assert ad_obj.get_loggedin_user_display_name() == 'ADReset Service Account'

    @manage_mock_ldap
    def test_get_ldap_attribute(self):
        assert self.ad_obj.svc_account_login() is True
        self.ad_obj.get_ldap_attribute('Domain Users', 'distinguishedName') == 'CN=Domain Users,CN=Users,DC=example,DC=local'

    @manage_mock_ldap
    def test_get_domain_ldap_attribute(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.get_domain_ldap_attribute('objectSid') == '\x01\x04\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00=\x12\xb7KE\xa7\x8d\xe2wZ\xff\xb3'

    @manage_mock_ldap
    def test_get_distinguished_name(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.get_distinguished_name('Domain Users') == 'CN=Domain Users,CN=Users,DC=example,DC=local'

    @manage_mock_ldap
    def test_get_user_email(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.get_user_email('user1') == 'user1@example.local'

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\user1')
    # Mocks the search results as this is a AD only search query
    @patch('mockldap.ldapobject.LDAPObject.search_s', return_value=mocked_nested_group_members_query())
    # Since search_s is patched, get_distinguished_name needs to be patched as otherwise it would call the patched
    # version of search_s
    @patch('adreset2.utils.AD.get_distinguished_name', return_value='CN=user1,CN=Users,DC=example,DC=local')
    @manage_mock_ldap
    def test_get_nested_group_members(self, mock_nested_group_members_query, mock_whoami_s, mock_get_distinguished_name):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.check_if_nested_group_member('user1', 'CN=ADReset Admins,OU=Groups,DC=example,DC=local') is True

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\user1')
    @manage_mock_ldap
    def test_get_primary_group_dn_of_user(self, mock_whoami_s):
        assert self.ad_obj.get_primary_group_dn_of_user('user1') == 'cn=domain users,cn=users,dc=example,dc=local'

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\user1')
    # Simpler to patch this in order to reduce the overall amount of patches
    @patch('adreset2.utils.AD.check_if_nested_group_member', return_value=True)
    @manage_mock_ldap
    def test_check_group_membership_memberof_pass(self, mock_nested_group_members_query, mock_whoami_s):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.check_group_membership('user1', 'ADReset Admins') is True

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\user2')
    # Simpler to patch this in order to reduce the overall amount of patches
    @patch('adreset2.utils.AD.check_if_nested_group_member', return_value=False)
    @manage_mock_ldap
    def test_check_group_membership_primary_group_pass(self, mock_nested_group_members_query, mock_whoami_s):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.check_group_membership('user2', 'ADReset Admins') is True

    # Mocks the actual value returned from AD versus another LDAP directory
    @patch('mockldap.ldapobject.LDAPObject.whoami_s', return_value='EXAMPLE\\svcADReset')
    # Simpler to patch this in order to reduce the overall amount of patches
    @patch('adreset2.utils.AD.check_if_nested_group_member', return_value=False)
    @manage_mock_ldap
    def test_check_group_membership_memberof_fail(self, mock_nested_group_members_query, mock_whoami_s):
        assert self.ad_obj.svc_account_login() is True
        with pytest.raises(ADException) as excinfo:
            self.ad_obj.check_group_membership('svcADReset', 'ADReset Admins')
        assert excinfo.value.message == 'The user account is not authorized to login to ADReset2'

    @manage_mock_ldap
    def test_unlock_user(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.unlock_user('locked_user') is True
        assert self.ad_obj.get_ldap_attribute('locked_user', 'lockoutTime') == '0'

    @manage_mock_ldap
    def test_reset_user_password(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.reset_user_password('user1', 'NewP@ssw0rd') is True
        # This would be invalid when used against AD, but this is just to make sure attribute has changed
        assert self.ad_obj.get_ldap_attribute('user1', 'unicodePwd') == '"NewP@ssw0rd"'.encode("utf-16-le")

    @manage_mock_ldap
    def test_is_account_disabled_true(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.is_account_disabled('disabled_user') is True

    @manage_mock_ldap
    def test_get_min_password_length(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.get_min_password_length() == 7

    @manage_mock_ldap
    def test_is_pw_complexity_required(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.is_pw_complexity_required() is True

    @manage_mock_ldap
    def test_match_min_pwd_length_true(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.match_min_pwd_length('LongishPassw0rd') is True

    @manage_mock_ldap
    def test_match_min_pwd_length_false(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.match_min_pwd_length('123') is False

    @manage_mock_ldap
    def test_match_password_complexity_true(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.match_password_complexity('P@ssw0rd123') is True

    @manage_mock_ldap
    def test_match_password_complexity_false(self):
        assert self.ad_obj.svc_account_login() is True
        assert self.ad_obj.match_password_complexity('password') is False

    @manage_mock_ldap
    def test_sid2str(self):
        assert self.ad_obj.sid2str('\x01\x04\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00=\x12\xb7KE\xa7\x8d\xe2wZ\xff\xb3')\
            == 'S-1-5-21-1270288957-3800934213-3019856503'
