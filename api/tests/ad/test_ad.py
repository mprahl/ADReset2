# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import mock
from mock import PropertyMock
import pytest
import ldap3

import adreset.ad


# Note that we can't login to LDAP using AD syntax, we must use the whole distinguished name
def test_login(mock_ad):
    """Test the AD.login method."""
    # Make sure no exception is thrown
    assert mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd') is None


def test_search(mock_ad):
    """Test that AD.search returns the correct results."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    rv = mock_ad.search('(sAMAccountName=testuser2)', attributes=['userPrincipalName'])
    assert rv == [
        {
            'attributes': {
                'userPrincipalName': 'testuser2@adreset.local'
            },
            'dn': 'CN=testuser2,OU=ADReset,DC=adreset,DC=local',
            'raw_attributes': {
                'userPrincipalName': [b'testuser2@adreset.local']
            },
            'raw_dn': b'CN=testuser2,OU=ADReset,DC=adreset,DC=local',
            'type': 'searchResEntry'
        }
    ]


def test_get_attribute(mock_ad):
    """Test that AD.get_attribute returns the correct result."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.get_attribute('testuser2', 'userPrincipalName') == 'testuser2@adreset.local'


def test_get_domain_attribute(mock_ad):
    """Test that AD.get_domain_attribute returns the correct result."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.get_domain_attribute('minPwdLength') == 7


def test_get_min_pwd_length(mock_ad):
    """Test that AD.min_pwd_length returns the correct result."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.min_pwd_length == 7


def test_get_pw_complexity_required(mock_ad):
    """Test that AD.pw_complexity_required returns the correct result."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.pw_complexity_required is True


@pytest.mark.parametrize('password,complexity_required,expected', [
    ('P@ssw0rd123', True, True),
    ('P@ssw0rd123', False, True),
    ('p@ssword123', True, True),
    ('p@ssword123', False, True),
    ('Password123', True, True),
    ('Password123', False, True),
    ('password123', True, False),
    ('password123', False, True),
    ('password', True, False),
    ('password', False, True)
])
def test_match_pwd_complexity(password, complexity_required, expected, mock_ad):
    """Test the AD.match_pwd_complexity method."""
    with mock.patch('adreset.ad.AD.pw_complexity_required', new_callable=PropertyMock,
                    return_value=complexity_required):
        assert mock_ad.match_pwd_complexity(password) is expected


@pytest.mark.parametrize('password,length_policy,expected', [
    ('password', 8, True),
    ('password123', 8, True),
    ('pass', 8, False)
])
def test_match_min_pwd_length(password, length_policy, expected, mock_ad):
    """Test the AD.match_min_pwd_length method."""
    with mock.patch('adreset.ad.AD.min_pwd_length', new_callable=PropertyMock,
                    return_value=length_policy):
        assert mock_ad.match_min_pwd_length(password) is expected


def test_get_guid(mock_ad):
    """Test that the AD.get_guid method returns a GUID in string format."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.get_guid('testuser') == '5609c5ec-c0df-4480-a94b-b6eb0fc4c066'


def test_get_sam_account_name(mock_ad):
    """Test that the AD.get_sam_account_name returns a username."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.get_sam_account_name('5609c5ec-c0df-4480-a94b-b6eb0fc4c066') == 'testuser'


def test_get_loggedin_user(mock_ad):
    """Test that the AD.get_loggedin_user returns the logged in user."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.get_loggedin_user() == 'testuser'


def test_reset_password(mock_ad):
    """Test the AD.reset_password method."""
    mock_ad.login('CN=testuser,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    # ldap3's mock directory doesn't actually reset the password so we can only test that
    # no exceptions were raised
    assert mock_ad.reset_password('lockedUser', 'NewP@ssw0rd') is None
    # We can verify that the lockoutTime was reset
    assert str(mock_ad.get_attribute('lockedUser', 'lockoutTime')) == '1601-01-01 00:00:00+00:00'


class MockLDAPConnection(object):
    """Mock ldap3.Connection."""

    def __init__(self, search_side_effect):
        """Initialize the mock ldap3 Connection."""
        self.search_side_effect = search_side_effect
        self.bound = True
        self.authentication = ldap3.NTLM
        self.username = None
        self.password = None
        self.response = None

    def open(self):
        """Open the connection."""
        pass

    def unbind(self):
        """Unbind the connection."""
        self.bound = False

    def search(self, *args, **kwargs):
        """Search LDAP and set self.response."""
        self.response = self.search_side_effect.pop(0)
        return True


def test_check_group_membership_nested():
    """Test the AD.check_group_membership method."""
    search_side_effect = [
        [{'attributes': {'distinguishedName': 'CN=ADReset Users,OU=Groups,DC=adreset,DC=local'}}],
        [
            {'attributes': {'sAMAccountName': 'testuser'}},
            {'attributes': {'sAMAccountName': 'tbrady'}}
        ]
    ]
    mock_conn_rv = MockLDAPConnection(search_side_effect)
    with mock.patch('ldap3.Server'):
        with mock.patch('ldap3.Connection', return_value=mock_conn_rv):
            # AD.log will make calls to AD to get the display name, so just mock that
            with mock.patch('adreset.ad.AD.log'):
                ad = adreset.ad.AD()
                assert ad.check_group_membership('testuser', 'ADReset Users') is True


@pytest.mark.parametrize('primary_group,expected', [
    ('ADReset Users', True),
    ('Some Group', False)
])
def test_check_group_membership_primary_group(primary_group, expected):
    """Test the AD.check_group_membership method when the group is the primary group."""
    group_dn_base = 'CN={0},OU=Groups,DC=adreset,DC=local'
    search_side_effect = [
        [{'attributes': {'distinguishedName': group_dn_base.format('ADReset Users')}}],
        [
            {'attributes': {'sAMAccountName': 'thanks'}},
            {'attributes': {'sAMAccountName': 'tbrady'}}
        ],
        [{'attributes': {'primaryGroupID': 1607}}],
        [{'attributes': {'objectSid': 'S-1-5-21-1270288957-3800934213-3019856503'}}],
        [{'attributes': {'distinguishedName': group_dn_base.format(primary_group)}}]
    ]
    mock_conn_rv = MockLDAPConnection(search_side_effect)
    with mock.patch('ldap3.Server'):
        with mock.patch('ldap3.Connection', return_value=mock_conn_rv):
            # AD.log will make calls to AD to get the display name, so just mock that
            with mock.patch('adreset.ad.AD.log'):
                ad = adreset.ad.AD()
                assert ad.check_group_membership('testuser', 'ADReset Users') is expected
