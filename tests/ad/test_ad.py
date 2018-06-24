# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals


# Note that we can't login to LDAP using AD syntax, we must use the whole distinguished name
def test_login(mock_ad):
    """Test the AD.login method."""
    # Make sure no exception is thrown
    assert mock_ad.login('CN=Test User,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd') is None


def test_search(mock_ad):
    """Test that AD.search returns the correct results."""
    mock_ad.login('CN=Test User,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    rv = mock_ad.search('(sAMAccountName=testUser2)', attributes=['userPrincipalName'])
    assert rv == [
        {
            'attributes': {
                'userPrincipalName': 'testUser2@adreset.local'
            },
            'dn': 'CN=testUser2,OU=ADReset,DC=adreset,DC=local',
            'raw_attributes': {
                'userPrincipalName': [b'testUser2@adreset.local']
            },
            'raw_dn': b'CN=testUser2,OU=ADReset,DC=adreset,DC=local',
            'type': 'searchResEntry'
        }
    ]


def test_get_guid(mock_ad):
    """Test that the AD.get_guid method returns a GUID in string format."""
    mock_ad.login('CN=Test User,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    assert mock_ad.get_guid('testuser') == '5609c5ec-c0df-4480-a94b-b6eb0fc4c066'


def test_get_loggedin_user(mock_ad):
    """Test that the AD.get_loggedin_user returns the logged in user."""
    mock_ad.login('CN=Test User,OU=ADReset,DC=adreset,DC=local', 'P@ssW0rd')
    # AD would normally return the format of DOMAIN\USER, and the method would return just the user,
    # but ldap3 mocking doesn't support that format.
    assert mock_ad.get_loggedin_user() == 'CN=Test User,OU=ADReset,DC=adreset,DC=local'
