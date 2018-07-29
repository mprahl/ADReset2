# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import ldap3
from ldap3.core.exceptions import LDAPSocketOpenError
from flask import current_app

from adreset.error import ConfigurationError, ADError, ValidationError
from adreset import log


class AD(object):
    """Abstract the Active Directory tasks for the app."""

    unknown_error_msg = ('An unknown issue was encountered. Please contact the administrator for '
                         'help.')
    failed_search_error = ('An error occured while searching Active Directory. Please contact the '
                           'administrator for help.')

    def __init__(self):
        """Initialize the AD class."""
        self._connection = None

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
        logged_in_user = self.get_loggedin_user(raise_exc=False)
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
        try:
            config = current_app.config[config_name]
        except KeyError:
            self.log('error', 'The configuration option "{0}" is not set'.format(config_name))
            if raise_exc:
                raise config_error

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

        if not self.connection.bind():
            self.log('info', 'The user "{0}" failed to login'.format(self.connection.user))
            raise ValidationError('The username or password is incorrect. Please try again.')
        else:
            self.log('info', 'The user "{0}" logged in successfully'.format(self.connection.user))

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

    def get_guid(self, sam_account_name):
        """
        Get an object's GUID (unique identifier across the AD Forest).

        :param str sam_account_name: the sAMAccountName of the LDAP object to search for
        :return: the object's GUID in string format
        :rtype: str
        """
        search_filter = '(sAMAccountName={0})'.format(sam_account_name)
        results = self.search(search_filter, attributes=['objectGuid'])
        # ldap3 returns the GUID surrounded by curly braces for whatever reason, so remove that
        return results[0]['attributes']['objectGuid'].strip('{}')
