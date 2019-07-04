# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from datetime import datetime, timedelta, timezone
import re

import ldap3
from ldap3.core.exceptions import LDAPSocketOpenError
from flask import current_app
from werkzeug.exceptions import Unauthorized

from adreset.error import ConfigurationError, ADError, ValidationError
from adreset import log


class AD(object):
    """Abstract the Active Directory tasks for the app."""

    # Active Directory stores timestamps in "filetime". When the value is zero in Active Directory,
    # that is the equivalent of January 1st, 1601.
    min_filetime = datetime(1601, 1, 1, tzinfo=timezone.utc)
    unknown_error_msg = ('An unknown issue was encountered. Please contact the administrator for '
                         'help.')
    failed_search_error = ('An error occured while searching Active Directory. Please contact the '
                           'administrator for help.')

    def __init__(self):
        """Initialize the AD class."""
        self._connection = None
        # Cache the minimum password length to avoid getting the value from AD multiple times
        self._min_pwd_length = None

    def __del__(self):
        """Disconnect from Active Directory."""
        if self._connection:
            self._connection.unbind()

    def log(self, category, message, **kwarg):
        """
        Log a message which includes the current logged in user.

        :param str category: the log message category
        :param str message: the log message
        :kwarg any **kwarg: any keyword arguments to pass on to the logger
        """
        log_method = getattr(log, category)
        # Only get the logged-in user info if the connection is bound
        if self._connection and self._connection.bound:
            logged_in_user = self.get_loggedin_user(raise_exc=False)
        else:
            logged_in_user = None
        log_method({'message': message, 'user': logged_in_user}, **kwarg)

    def _get_config(self, config_name, raise_exc=True):
        """
        Get a configuration item from the Flask configuration and do some validation.

        :param str config_name: the configuration item to get
        :kwarg bool raise_exc: raise an exception if there is an error
        :return: the configuration item in the Flask configuration
        :rtype: any
        :raises ConfigurationError: if the configuration item isn't set or is invalid
        """
        config_error = ConfigurationError(
            'The application has a configuration error. Ask the administrator to check the logs.')
        if config_name in current_app.config:
            config = current_app.config[config_name]
        else:
            self.log('error', 'The configuration option "{0}" is not set'.format(config_name))
            if raise_exc:
                raise config_error
            return None

        if config_name == 'AD_LDAP_URI' and not config.startswith('ldaps://'):
            self.log('error', 'LDAPS is not set and is required. Please reconfigure "AD_LDAP_URI".')
            if raise_exc:
                raise config_error

        return config

    @property
    def connection(self):
        """
        Return an unauthenticated LDAP connection to Active Directory.

        :return: an LDAP connection to Active Directory
        :rtype: ldap3.Connection
        """
        if self._connection:
            return self._connection

        ldap_url = self._get_config('AD_LDAP_URI')
        server = ldap3.Server(ldap_url, allowed_referral_hosts=[('*', False)], connect_timeout=3)
        self._connection = ldap3.Connection(server)

        if self._get_config('AD_USE_NTLM', raise_exc=False):
            msg = 'Configuring the Active Directory connection to use NTLM authentication'
            self.log('debug', msg)
            self._connection.authentication = ldap3.NTLM
        else:
            msg = 'Configuring the Active Directory connection to use SIMPLE authentication'
            self.log('debug', msg)
            self._connection.authentication = ldap3.SIMPLE

        try:
            msg = 'Connecting to Active Directory with the URL "{0}"'.format(ldap_url)
            self.log('debug', msg)
            self._connection.open()
        except LDAPSocketOpenError:
            msg = 'The connection to Active Directory with the URL "{0}" failed'.format(ldap_url)
            self.log('error', msg, exc_info=True)
            raise ADError('The connection to Active Directory failed. Please try again.')

        return self._connection

    @property
    def base_dn(self):
        """Return the base distinguished name (e.g. DC=adreset,DC=local)."""
        return 'DC=' + (self._get_config('AD_DOMAIN').replace('.', ',DC='))

    def login(self, username, password):
        """
        Login to Active Directory.

        :param str username: the Active Directory username
        :param str password: the Active Directory password
        """
        if self.connection.bound:
            msg = 'The login method was called but the connection is already bound. Will reconnect.'
            self.log('debug', msg)
            self.connection.unbind()
            self.connection.open()

        domain = self._get_config('AD_DOMAIN')
        if '@' in username or '\\' in username or 'CN=' in username:
            self.connection.user = username
        else:
            if self.connection.authentication == ldap3.NTLM:
                self.connection.user = '{0}\\{1}'.format(domain, username)
            else:
                self.connection.user = '{0}@{1}'.format(username, domain)
        self.connection.password = password

        svc_account = self._get_config('AD_SERVICE_USERNAME') == username
        if not self.connection.bind():
            if svc_account:
                self.log('error', 'The service account failed to login')
                raise ADError(self.unknown_error_msg)
            else:
                self.log('info', 'The user "{0}" failed to login'.format(self.connection.user))
                raise Unauthorized('The username or password is incorrect. Please try again.')
        else:
            if svc_account:
                self.log('info', 'The service account logged in successfully')
            else:
                self.log('info', 'The user logged in successfully')

    def service_account_login(self):
        """Login using the configured service account."""
        self.login(self._get_config('AD_SERVICE_USERNAME'), self._get_config('AD_SERVICE_PASSWORD'))

    def get_loggedin_user(self, raise_exc=True):
        """
        Get the logged in user's username.

        :kwarg bool raise_exc: raise an exception if the connection isn't bound
        :return: a the logged in user's user name
        :rtype: str
        """
        if self.connection.bound:
            user = self.connection.extend.standard.who_am_i()
            if not self._get_config('TESTING', raise_exc=False):
                # AD returns the username as DOMAIN\username, so this gets the sAMAccountName
                return user.split('\\')[-1]
            else:
                # We are using ldap3's mocking, which returns the distinguished name, so derive the
                # sAMAccountName from that
                return user.split('CN=')[-1].split(',')[0]

        elif raise_exc:
            self.log('error', 'You must be logged in to get the logged in user\'s username')
            raise ADError(self.unknown_error_msg)

    def search(self, search_filter, attributes=None, search_scope=ldap3.SUBTREE, raise_exc=True):
        """
        Search Active Directory using an LDAP filter.

        :param str search_filter: the LDAP search filter to use
        :kwarg list attributes: a list of LDAP attributes to search for
        :kwarg str search_scope: the LDAP search scope to use
        :kwarg bool raise_exc: raise an exception if the search yields no results
        :return: the ldap3 formatted response from Active Directory
        :rtype: list
        """
        if not self.connection.bound:
            raise ADError('You must be logged into LDAP to search')
        msg = ('Searching Active Directory with "{0}" and the following attributes: {1}'
               .format(search_filter, ', '.join(attributes or [])))
        self.log('debug', msg)

        try:
            search_succeeded = self.connection.search(
                self.base_dn, search_filter, search_scope=search_scope, attributes=attributes)
        except ldap3.core.exceptions.LDAPAttributeError:
            msg = ('An invalid LDAP attribute was requested when searching for "{0}" with '
                   'attributes: {1}').format(search_filter, ', '.join(attributes))
            self.log('error', msg, exc_info=True)
            raise ADError(self.failed_search_error)

        if search_succeeded and self.connection.response:
            return self.connection.response

        self.log('error', 'The search for "{0}" did not yield any results'.format(search_filter))
        if raise_exc:
            raise ADError(self.failed_search_error)

    def _get_attributes(self, search_filter, attributes):
        """
        Get the attributes of the first LDAP object returned from the search filter.

        :param str search_filter: the LDAP search filter to use
        :param list attributes: the attributes from the domain to search for
        :rtype: dict
        :return: the dictionary of attributes, where the keys are the attribute names and
            the values are the attribute values
        """
        results = self.search(search_filter, attributes)

        if 'attributes' in results[0]:
            return {
                attribute: results[0]['attributes'][attribute]
                for attribute in attributes
            }

        return {}

    def get_attributes(self, sam_account_name, attributes):
        """
        Get an LDAP attribute from the object.

        :param str sam_account_name: the sAMAccountName of the LDAP object to search for
        :param list attributes: the list of attributes of the LDAP object to search for
        :rtype: dict
        :return: the dictionary of attributes, where the keys are the attribute names and
            the values are the attribute values
        """
        search_filter = '(sAMAccountName={0})'.format(sam_account_name)
        result = self._get_attributes(search_filter, attributes)
        if not result:
            self.log(
                'error',
                'The LDAP attribute(s) {0} for "{1}" couldn\'t be found'
                .format(', '.join(attributes), sam_account_name)
            )

        return result

    def get_attribute(self, sam_account_name, attribute):
        """
        Get an LDAP attribute from the object.

        :param str sam_account_name: the sAMAccountName of the LDAP object to search for
        :param str attribute: the attribute of the LDAP object to search for
        :rtype: any
        :return: the attribute of the LDAP object
        """
        return self.get_attributes(sam_account_name, [attribute]).get(attribute)

    def get_domain_attributes(self, attributes):
        """
        Get LDAP attributes from the domain.

        :param list attributes: the attributes from the domain to search for
        :rtype: dict
        :return: the dictionary of domain attributes, where the keys are the attribute names and
            the values are the attribute values
        """
        search_filter = '(&(objectClass=domainDNS))'
        result = self._get_attributes(search_filter, attributes)
        if not result:
            self.log(
                'error',
                'The LDAP attribute(s) {0} on the domain couldn\'t be found'
                .format(', '.join(attributes))
            )

        return result

    def get_domain_attribute(self, attribute):
        """
        Get an LDAP attribute from the domain.

        :param str attribute: the attribute from the domain to search for
        :rtype: any
        :return: the domain attribute
        """
        return self.get_domain_attributes([attribute]).get(attribute)

    def get_guid(self, sam_account_name):
        """
        Get an object's GUID (unique identifier across the AD Forest).

        :param str sam_account_name: the sAMAccountName of the LDAP object to search for
        :return: the object's GUID in string format
        :rtype: str
        """
        guid = self.get_attribute(sam_account_name, 'objectGUID')
        if guid:
            # ldap3 returns the GUID surrounded by curly braces for whatever reason, so remove that
            return guid.strip('{}')

    def get_dn(self, sam_account_name):
        """
        Get an object's distinguished name.

        :param str sam_account_name: the sAMAccountName of the LDAP object to search for
        :return: the objet's distinguished name
        :rtype: str
        """
        return self.get_attribute(sam_account_name, 'distinguishedName')

    def get_sam_account_name(self, guid):
        """
        Get a user's distinguished name from their GUID.

        :param str guid: the GUID of the user to search for
        :return: the user's sAMAccountNmae
        :rtype: str
        """
        search_filter = '(&(objectClass=user)(objectGUID={0}))'.format(guid)
        results = self.search(search_filter, ['sAMAccountName'])

        if 'attributes' in results[0]:
            return results[0]['attributes']['sAMAccountName']
        else:
            self.log(
                'error',
                'The user with the GUID {0} couldn\'t be found in Active Directory'.format(guid))
            raise ADError('The user couldn\'t be found in Active Directory')

    @property
    def min_pwd_length(self):
        """
        Get the domain's minimum password length.

        :rtype: int
        :return: the minimum length a password must be
        """
        if self._min_pwd_length is None:
            self._min_pwd_length = self.get_domain_attribute('minPwdLength')
        return int(self._min_pwd_length)

    @property
    def pw_complexity_required(self):
        """
        Return if the domain requires complex passwords.

        :rtype: bool
        :return: a boolean specifying if the domain requires complex passwords
        """
        return bool(self.get_domain_attribute('pwdProperties'))

    def match_min_pwd_length(self, password):
        """
        Determine if a password meets the domain's length requirements.

        :rtype: bool
        :return: a boolean specifying if the password meets the length requirements
        """
        return len(password) >= self.min_pwd_length

    def match_pwd_complexity(self, password):
        """
        Determine if the password matches the complexity required by the domain.

        :param str password: the password to check
        :rtype: bool
        :return: if the password matches the complexity required by the domain
        """
        if self.pw_complexity_required:
            complexity_score = 0
            # If a capital letter is found in the password
            if re.search(r'[A-Z]', password):
                complexity_score += 1
            # If a lowercase letter is found in the password
            if re.search(r'[a-z]', password):
                complexity_score += 1
            # If a digit is found in the password
            if re.search(r'\d', password):
                complexity_score += 1
            # If a nonletter or number is found in the password (should match any special character)
            if re.search(r'\W', password):
                complexity_score += 1

            return complexity_score >= 3
        else:
            return True

    def reset_password(self, sam_account_name, new_password):
        """
        Reset and unlock a user's password.

        :param str sam_account_name: the user's sAMAccountName to reset
        :param str new_password: the user's new password
        :raises ValidationError: if the new password doesn't meet the domain standards
        """
        if not self.match_pwd_complexity(new_password):
            raise ValidationError(
                'The password did not match the complexity requirements. Please ensure your '
                'password contains at least three of the four requirements: lowercase letters, '
                'uppercase letters, numbers, and special charcters.')
        elif not self.match_min_pwd_length(new_password):
            raise ValidationError('The password must be at least {0} characters long'.format(
                self.min_pwd_length))
        dn = self.get_dn(sam_account_name)
        self.connection.extend.microsoft.modify_password(dn, new_password, old_password=None)
        self.connection.extend.microsoft.unlock_account(dn)
        self.log('info', 'The password for "{0}" was reset'.format(self.connection.user))

    def check_group_membership(self, sam_account_name, group):
        """
        Check if the passed-in user is a member of this group (nested search).

        :param str sam_account_name: the user's sAMAccountName to check group membership
        :param str group: the group's sAMAccountName to check if the user is a member of
        :return: a boolean determining if the user is a member of this group
        :rtype: bool
        """
        group_dn = self.get_dn(group)
        # Start by seeing if the user is part of a nested group membership
        search_filter = ('(&(objectClass=user)(memberOf:1.2.840.113556.1.4.1941:={0}))'
                         .format(group_dn))
        results = self.search(search_filter, attributes=['sAMAccountName'])
        members = set(
            [user['attributes']['sAMAccountName'] for user in results if user.get('attributes')])
        if sam_account_name in members:
            return True

        # If the user isn't part of a nested group membership, check to see if the user's primary
        # group is the group in question
        primary_group_id = self.get_attribute(sam_account_name, 'primaryGroupID')
        domain_sid = self.get_domain_attribute('objectSid')
        search_filter = '(&(objectClass=group)(objectSid={0}-{1}))'.format(
            domain_sid, primary_group_id)
        results = self.search(search_filter, attributes=['distinguishedName'])
        if 'attributes' in results[0] and results[0]['attributes']['distinguishedName'] == group_dn:
            return True

        return False

    def check_user_group_membership(self, user_guid):
        """
        Check if the passed-in user is a regular user.

        :param str user_guid: the user's GUID to check group membership
        :return: a boolean determining if the user is a regular user
        :rtype: bool
        """
        user_groups = self._get_config('AD_USER_GROUPS')
        sam_account_name = self.get_sam_account_name(user_guid)
        return any(self.check_group_membership(sam_account_name, group) for group in user_groups)

    def check_admin_group_membership(self, user_guid):
        """
        Check if the passed-in user is an admin.

        :param str user_guid: the user's GUID to check group membership
        :return: a boolean determining if the user is an admin
        :rtype: bool
        """
        admin_groups = self._get_config('AD_ADMIN_GROUPS')
        sam_account_name = self.get_sam_account_name(user_guid)
        return any(self.check_group_membership(sam_account_name, group) for group in admin_groups)

    @staticmethod
    def is_pwd_never_expires_set(user_account_control):
        """
        Determine if the "password never expires" flag is set.

        :param int user_account_control: the userAccountControl LDAP attribute value of the user
        :return: a boolean determining if the "password never expires" flag is set
        :rtype: bool
        """
        # See https://support.microsoft.com/en-us/help/305144/how-to-use-useraccountcontrol-to-manipulate-user-account-properties # noqa: E501
        return (user_account_control & 65536) == 65536

    @staticmethod
    def is_account_disabled(user_account_control):
        """
        Determine if the account is disabled.

        :param int user_account_control: the userAccountControl LDAP attribute value of the user
        :return: a boolean determining if the account is disabled
        :rtype: bool
        """
        # See https://support.microsoft.com/en-us/help/305144/how-to-use-useraccountcontrol-to-manipulate-user-account-properties # noqa: E501
        return (user_account_control & 2) == 2

    @staticmethod
    def is_account_locked_out(lockout_time, lockout_duration):
        """
        Determine if the account is locked out.

        :param datetime.datetime lockout_time: the datetime representation of the lockoutTime
            LDAP attribute
        :param datetime.datetime lockout_duration: the timedelta representation of the
            lockoutDuration LDAP attribute
        :return: a boolean determining if the account is locked out
        :rtype: bool
        """
        # If password lockouts are disabled on the domain, this can be falsey
        if not lockout_time:
            return False

        return lockout_time + lockout_duration > datetime.now(timezone.utc)

    @staticmethod
    def get_unlock_date(lockout_time, lockout_duration):
        """
        Determine when the account will be unlocked.

        None is returned when the account is not locked out.

        :param datetime.datetime lockout_time: the datetime representation of the lockoutTime
            LDAP attribute
        :param datetime.datetime lockout_duration: the timedelta representation of the
            lockoutDuration LDAP attribute
        :return: the datetime of when the user's account will be unlocked
        :rtype: datetime.datetime or None
        """
        if AD.is_account_locked_out(lockout_time, lockout_duration):
            return lockout_time + lockout_duration

    @staticmethod
    def get_pwd_expiration_date(max_pwd_age, pwd_last_set, user_account_control):
        """
        Determine when the user's password expires.

        When None is returned, it can mean a few things. It can mean the pwdLastSet LDAP attribute
        is not set. This usually means an Active Directory administrator set the password to expire
        at next logon. It can also mean the domain doesn't expire passwords, or the user has their
        password set to never expire.

        :param datetime.timedelta max_pwd_age: the timedelta representation of the maxPwdAge
            LDAP attribute of the domain
        :param datetime.datetime pwd_last_set: the datetime representation of the pwdLastSet LDAP
            attribute of the user
        :param int user_account_control: the userAccountControl LDAP attribute value of the user
        :return: the datetime of when the user's password expires
        :rtype: datetime.datetime or None
        """
        # TODO: `max_pwd_age == timedelta.max` relies on:
        # https://github.com/cannatag/ldap3/pull/708
        if (
            max_pwd_age == timedelta.max
            or pwd_last_set == AD.min_filetime
            or AD.is_pwd_never_expires_set(user_account_control)
        ):
            return None

        return pwd_last_set + max_pwd_age

    @staticmethod
    def get_when_pwd_can_be_set(min_pwd_age, pwd_last_set):
        """
        Determine when the user's password can be set next.

        When None is returned, it means the password can be set now.

        :param datetime.timedelta min_pwd_age: the timedelta representation of the minPwdAge
            LDAP attribute of the domain
        :param datetime.datetime pwd_last_set: the datetime representation of the pwdLastSet LDAP
            attribute of the user
        :return: the datetime of when the user's password can be set next
        :rtype: datetime.datetime
        """
        if min_pwd_age == timedelta(0):
            return None

        when = pwd_last_set + min_pwd_age
        if when < datetime.now(timezone.utc):
            return None

        return when

    def get_account_status(self, sam_account_name):
        """
        Get general information about the account in the context of the domain.

        If the user can't be found in LDAP, None is returned.

        :param str sam_account_name: the sAMAccountName of the LDAP object to search for
        :return: a dictionary with general information about the account or None
        :rtype: dict or None
        """
        self.log('info', 'Getting the account status for {}'.format(sam_account_name))
        domain_attributes = self.get_domain_attributes(
            ['lockoutDuration', 'maxPwdAge', 'minPwdAge', 'minPwdLength', 'pwdProperties'],
        )
        user_attributes = self.get_attributes(
            sam_account_name,
            ['lockoutTime', 'pwdLastSet', 'userAccountControl'],
        )
        if not user_attributes:
            return

        last_set = user_attributes['pwdLastSet']
        if last_set == AD.min_filetime:
            last_set = None

        uac = user_attributes['userAccountControl']
        return {
            'account_is_disabled': self.is_account_disabled(uac),
            'account_is_locked_out': self.is_account_locked_out(
                user_attributes['lockoutTime'],
                domain_attributes['lockoutDuration'],
            ),
            'account_is_unlocked_on': self.get_unlock_date(
                user_attributes['lockoutTime'],
                domain_attributes['lockoutDuration'],
            ),
            'password_can_be_set_on': self.get_when_pwd_can_be_set(
                domain_attributes['minPwdAge'],
                user_attributes['pwdLastSet'],
            ),
            'password_expires_on': self.get_pwd_expiration_date(
                domain_attributes['maxPwdAge'],
                user_attributes['pwdLastSet'],
                uac,
            ),
            'password_last_set_on': last_set,
            'password_never_expires': self.is_pwd_never_expires_set(uac),
        }
