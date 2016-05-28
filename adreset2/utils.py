"""
Author: StackFocus
File: utils.py
Purpose: contains classes and functions for the application
"""
import ldap
from struct import unpack
from re import search, sub, IGNORECASE
from os import getcwd
from json import dumps
from datetime import datetime
from wtforms.validators import StopValidation as WtfStopValidation
from adreset2 import models, db, bcrypt
from adreset2.errors import ValidationError, ADException


def validate_wtforms_password(form, field):
    """ Validates the password from a wtforms object
    """
    username = form.username.data
    password = form.password.data

    if username and password:
        try:
            if form.auth_source.data == 'ADReset2 User':
                admin = models.Admins.query.filter_by(username=username, source='local').first()

                if admin is not None and bcrypt.check_password_hash(admin.password, password):
                    form.admin = admin
                else:
                    json_logger(
                        'auth', username,
                        'The administrator "{0}" entered an incorrect username or password'.format(
                            username))
                    raise WtfStopValidation('The username or password was incorrect')
            else:
                pass
        except ADException as e:
            raise WtfStopValidation(e.message)


def add_default_configuration_settings():
    """ Adds the default configuration settings to the database if they aren't present.
    This is to be used from manage.py when creating the database.
    """
    if not models.Configs.query.filter_by(setting='Local Account Minimum Password Length').first():
        min_pwd_length = models.Configs()
        min_pwd_length.setting = 'Local Account Minimum Password Length'
        min_pwd_length.value = '8'
        min_pwd_length.regex = '^([1-9]|[1][0-9]|[2][0-5])$'
        db.session.add(min_pwd_length)

    if not models.Configs.query.filter_by(setting='Change Auditing').first():
        login_auditing = models.Configs()
        login_auditing.setting = 'Change Auditing'
        login_auditing.value = 'False'
        login_auditing.regex = '^(True|False)$'
        db.session.add(login_auditing)

    if not models.Configs.query.filter_by(setting='Login Auditing').first():
        login_auditing = models.Configs()
        login_auditing.setting = 'Login Auditing'
        login_auditing.value = 'False'
        login_auditing.regex = '^(True|False)$'
        db.session.add(login_auditing)

    if not models.Configs.query.filter_by(setting='Log File').first():
        log_file = models.Configs()
        log_file.setting = 'Log File'
        log_file.regex = '^(.+)$'
        db.session.add(log_file)

    if not models.Configs.query.filter_by(setting='AD Administrative Group').first():
        ad_admin_group = models.Configs()
        ad_admin_group.setting = 'AD Administrative Group'
        db.session.add(ad_admin_group)

    if not models.Configs.query.filter_by(setting='AD Users Group').first():
        ad_group = models.Configs()
        ad_group.setting = 'AD Users Group'
        db.session.add(ad_group)

    if not models.Admins.query.first():
        admin = models.Admins().from_json(
            {'username': 'admin', 'password': 'ADReset2', 'name': 'Default Admin'})
        db.session.add(admin)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def login_auditing_enabled():
    """ Returns a bool based on if mail db auditing is enabled
    """
    auditing_setting = models.Configs.query.filter_by(
        setting='Login Auditing').first().value
    return auditing_setting == 'True'


def json_logger(category, admin, message):
    """
    Takes a category (typically error or audit), a log message and the responsible
    user. It then appends it with an ISO 8601 UTC timestamp to a JSON formatted log file
    """
    log_path = models.Configs.query.filter_by(setting='Log File').first().value
    if log_path and ((category == 'auth' and login_auditing_enabled()) or category == 'error'):
        try:
            with open(log_path, mode='a+') as log_file:
                log_file.write("{}\n".format(dumps(
                    {
                        'category': category,
                        'message': message,
                        'admin': admin,
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    },
                    sort_keys=True)))
                log_file.close()
        except IOError:
            raise ValidationError(
                'The log could not be written to "{0}". \
                Verify that the path exists and is writeable.'.format(
                    getcwd().replace('\\', '/') + '/' + log_path))


def get_wtforms_errors(form):
    """ Returns the errors from wtforms in a single string with new lines
    """
    i = 0
    error_messages = ''
    for field, errors in form.errors.items():
        for error in errors:
            # If this isn't the first error, add a new line for the next error
            if i != 0:
                error_messages += '\n'
            # If the error is from DataRequired, make the error more user friendly
            if 'This field is required' in error:
                error_messages += 'The {0} was not provided'.format(
                    getattr(form, field).label.text.lower())
            else:
                error_messages += error
            i += 1

    return error_messages


def try_ad_connection(dc, port, domain, username, password):
    """ Returns a boolean based on if the connection to Active Directory is successful
    """
    ldap_server = 'LDAPS://{0}:{1}'.format(dc, port)

    if dc and port and domain and username and password:
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        ldap_connection = ldap.initialize(ldap_server)
        ldap_connection.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        # Turn off referrals
        ldap_connection.set_option(ldap.OPT_REFERRALS, 0)

        if '@' in username or '\\' in username or search('CN=', username, IGNORECASE):
            bind_username = username
        else:
            bind_username = username + '@' + domain

        try:
            ldap_connection.simple_bind_s(
                bind_username,
                password
            )
            return True

        except ldap.INVALID_CREDENTIALS:
            raise ADException('The username or password was incorrect')
        except ldap.SERVER_DOWN:
            raise ADException('The LDAP server could not be contacted')
        except Exception:
            raise ADException('The connection to the LDAP server failed')

    return False


class AD(object):
    """ A class that handles all the Active Directory tasks for the Flask app
    """
    ldap_connection = None
    ldap_server = None
    domain = None
    ldap_svc_user = None
    ldap_svc_password = None
    ldap_users_group = None

    def __init__(self):
        """ The constructor that initializes the ldap_connection object
        """
        dc = models.AdConfigs().query.filter_by(setting='domain_controller').first()
        port = models.AdConfigs().query.filter_by(setting='port').first()
        domain = models.AdConfigs().query.filter_by(setting='domain').first()
        ldap_svc_user = models.AdConfigs().query.filter_by(setting='username').first()
        ldap_svc_password = models.AdConfigs().query.filter_by(setting='password').first()
        ldap_admin_group = models.Configs().query.filter_by(setting='AD Administrative Group').first()
        ldap_users_group = models.Configs().query.filter_by(setting='AD Users Group').first()

        if dc and port and domain and ldap_svc_user and ldap_svc_password:
            self.domain = domain.value
            self.ldap_svc_user = ldap_svc_user.value
            self.ldap_svc_password = ldap_svc_password.value
            self.ldap_admin_group = ldap_admin_group.value
            self.ldap_users_group = ldap_users_group.value

            self.ldap_server = 'LDAPS://{0}:{1}'.format(dc.value, port.value)
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            self.ldap_connection = ldap.initialize(self.ldap_server)
            self.ldap_connection.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            # Turn off referrals
            self.ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
        else:
            json_logger('error', 'NA', 'An Active Directory connection attempt was made but not all the required \
                settings were configured')
            raise ADException('The Active Directory connection is not configured')

    def __del__(self):
        """ The destructor that disconnects from LDAP
        """
        self.ldap_connection.unbind()

    def login(self, username, password):
        """ Uses the supplied username and password to bind to LDAP and returns a boolean
        """
        # If a UPN, domain, or distinguishedName was provided then use that, otherwise form the UPN
        if '@' in username or '\\' in username or search('CN=', username, IGNORECASE):
            bind_username = username
        else:
            bind_username = username + '@' + self.domain

        try:
            self.ldap_connection.simple_bind_s(
                bind_username,
                password
            )
            return True

        except ldap.INVALID_CREDENTIALS:
            json_logger(
                'auth', bind_username,
                'The administrator "{0}" entered an incorrect username or password via LDAP'.format(bind_username))
            raise ADException('The username or password was incorrect')
        except ldap.SERVER_DOWN:
            json_logger(
                'error', bind_username,
                'The LDAP server "{0}" could not be contacted'.format(self.ldap_server))
            raise ADException('The LDAP server could not be contacted')
        except Exception as e:
            json_logger(
                'error', bind_username,
                'The LDAP bind could not complete with the following message: {0}'.format(e.message))
            raise ADException('The connection to the LDAP server failed. Please try again.')

    def svc_account_login(self):
        """ Logs in using the service account defined in the database
        """
        return self.login(self.ldap_svc_user, self.ldap_svc_password)

    def get_loggedin_user(self):
        """ Returns the logged in username without the domain
        """
        # Check if the ldap_connection is in a logged in state
        if self.ldap_connection.whoami_s():
            # AD returns the username as DOMAIN\username, so this gets the sAMAccountName
            return sub(r'(^.*(?<=\\))', '', self.ldap_connection.whoami_s())

        return None

    def get_loggedin_user_display_name(self):
        """ Returns the display name or the object name if the display name is not available of the logged on user
        """
        # Check if the ldap_connection is in a logged in state
        username = self.get_loggedin_user()
        if username:
            # Get the base distinguished name based on the domain name
            base_dn = 'dc=' + (self.domain.replace('.', ',dc='))
            search_filter = '(&(objectClass=user)(sAMAccountName={0}))'.format(username)
            # Returns the displayName and name of the user
            result = self.ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, ['displayName', 'name'])

            # Make sure the search returned results
            if result and result[0][0] is not None:
                # Makes sure the displayName attribute was returned
                if 'displayName' in result[0][1]:
                    return result[0][1]['displayName'][0]
                elif 'name' in result[0][1]:
                    return result[0][1]['name'][0]
            else:
                json_logger(
                    'error', username,
                    'The display name of the user "{0}" could not be found'.format(username))
                raise ADException('There was an error searching the LDAP server. Please try again.')
        else:
            raise ADException('You must be logged into LDAP to search')

        return None

    def get_ldap_attribute(self, sAMAccountName, attribute):
        """ Returns an LDAP attribute of an LDAP object based on sAMAccountName
        """
        # Check if the ldap_connection is in a logged in state
        if self.ldap_connection.whoami_s():

            # Get the base distinguished name based on the domain name
            base_dn = 'dc=' + (self.domain.replace('.', ',dc='))
            search_filter = '(&(sAMAccountName={0}))'.format(sAMAccountName)
            search_result = self.ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE,
                                                          search_filter, [attribute])
            # Make sure the search returned results
            if search_result and search_result[0][0] and attribute in search_result[0][1]:
                return search_result[0][1][attribute][0]

            json_logger('error', 'NA',
                        'The attribute "{0}" of the user "{1}" could not be found'.format(attribute, sAMAccountName))
        else:
            json_logger('error', 'NA', 'The attribute of a user could not be found because \
                the AD object is not authenticated to Active Directory')

        raise ADException('There was an error searching the LDAP server. Please try again.')

    def get_domain_ldap_attribute(self, attribute):
        """ Returns the value of a desired LDAP attribute from the connected domain's object
        """
        # Check if the ldap_connection is in a logged in state
        if self.ldap_connection.whoami_s():

            base_dn = 'dc=' + (self.domain.replace('.', ',dc='))
            search_filter = '(&(objectClass=domainDNS))'
            result = self.ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, [attribute])

            if result and result[0][0]:
                if attribute in result[0][1]:
                    return result[0][1][attribute][0]
                else:
                    return None

            json_logger('error', 'NA',
                        'The attribute "{0}" of the domain could not be found').format(attribute)
        else:
            json_logger('error', 'NA', 'The attribute of a user could not be found because \
                the AD object is not authenticated to Active Directory')

        raise ADException('There was an error searching the LDAP server. Please try again.')

    def get_distinguished_name(self, sAMAccountName):
        """ Gets the distinguishedName of an LDAP object based on the sAMAccountName
        """
        return self.get_ldap_attribute(sAMAccountName, 'distinguishedName')

    def get_user_email(self, sAMAccountName):
        """ Gets the mail attribute of a user based on the sAMAccountName
        """
        return self.get_ldap_attribute(sAMAccountName, 'mail')

    def check_if_nested_group_member(self, user_sAMAccountName, group_distinguishedName):
        """ Checks the members and nested members of a group by supplying a distinguishedName for the group and a
        user's sAMAccountName. A boolean based on membership will be returned
        """
        # Check if the ldap_connection is in a logged in state
        if self.ldap_connection.whoami_s():

            if user_sAMAccountName and group_distinguishedName:
                user_dn = self.get_distinguished_name(user_sAMAccountName)
                # Get the base distinguished name based on the domain name
                base_dn = 'dc=' + (self.domain.replace('.', ',dc='))
                search_filter = '(memberOf:1.2.840.113556.1.4.1941:={0})'.format(group_distinguishedName)
                search_result = self.ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE,
                                                              search_filter, ['distinguishedName'])
                for member in search_result:
                    if user_dn == member[0]:
                        return True
            return False
        else:
            raise ADException('You must be logged into LDAP to search')

    def get_primary_group_dn_of_user(self, sAMAccountName):
        """ Returns the distinguished name of the primary group of the user
        """
        # Check if the ldap_connection is in a logged in state
        if self.get_loggedin_user():
            if sAMAccountName:
                # Get the base distinguished name based on the domain name
                base_dn = 'dc=' + (self.domain.replace('.', ',dc='))
                primary_group_id = self.get_ldap_attribute(sAMAccountName, 'primaryGroupID')
                domain_sid = self.get_domain_ldap_attribute('objectSid')

                search_filter = '(&(objectClass=group)(objectSid={0}-{1}))'.format(
                    self.sid2str(domain_sid), primary_group_id)
                primary_group_result = self.ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE,
                                                                     search_filter, ['distinguishedName'])
                if primary_group_result and primary_group_result[0][0]:
                    return primary_group_result[0][0]
            return None
        else:
            raise ADException('You must be logged into LDAP to search')

    def check_group_membership(self, username, ldap_group):
        """ Checks the group membership of the logged on user. This will return True if the user is a member of
        the Administrator group set in the database
        """
        # Check if the ldap_connection is in a logged in state
        if self.ldap_connection.whoami_s():
            # Get the distinguished name of the admin group in the database
            group_distinguished_name = self.get_distinguished_name(ldap_group)

            if not group_distinguished_name:
                json_logger(
                    'error', username,
                    'The Active Directory group "{0}" could not be found'.format(ldap_group))
                raise ADException('There was an error searching LDAP. Please try again.')

            if self.check_if_nested_group_member(username, group_distinguished_name):
                return True

            # If the user was not a member of the group, check to see if the admin group is the primary group
            # of the user which is not included in memberOf (this is typically Domain Users)
            primary_group_dn = self.get_primary_group_dn_of_user(username)
            if primary_group_dn and group_distinguished_name.upper() == primary_group_dn.upper():
                return True

            json_logger(
                'auth', username,
                'The LDAP user "{0}" authenticated but the login failed \
                because they weren\'t a member of the group "{1}'.format(username, ldap_group))
            raise ADException('The user account is not authorized to login to ADReset2')
        else:
            raise ADException('You must be logged into LDAP to search')

    def unlock_user(self, sAMAccountName):
        """ Unlocks an Active Directory user when they are locked out of their account
        """
        user_dn = self.get_distinguished_name(sAMAccountName)

        if user_dn:
            try:
                # Unlock the account
                self.ldap_connection.modify_s(user_dn, [(ldap.MOD_REPLACE, 'lockoutTime', '0')])
                json_logger('audit', 'NA',
                            'The user "{0}" had their account unlocked successfully'.format(sAMAccountName))
                return True
            except Exception as e:
                json_logger('error', 'NA', 'The account unlock for the user "{0}" failed due to the \
                    following: "{1}"'.format(sAMAccountName, e.message))
                raise ADException('The account could not be unlocked due to an unexpected error. Please try again.')
        else:
            json_logger('error', 'NA', 'The distinguished name could not be found for the user \
                "{0}'.format(sAMAccountName))
            raise ADException('The user could not be found in Active Directory. Please try again.')

    def reset_user_password(self, sAMAccountName, password):
        """ Resets an Active Directory user's password
        """
        user_dn = self.get_distinguished_name(sAMAccountName)

        if user_dn:
            # Active Directory requires the password be surround by quotes and be unicode encoded
            encoded_password = ('"{0}"'.format(password)).encode("utf-16-le")
            try:
                # Set the password
                self.ldap_connection.modify_s(user_dn, [(ldap.MOD_REPLACE, 'unicodePwd', encoded_password)])
            except ldap.UNWILLING_TO_PERFORM:
                raise ADException('The password could not be reset because it did not meeting your organization\'s \
                    standards. Please try again.')
            except Exception as e:
                json_logger('error', 'NA', 'The password reset for the user "{0}" failed due to the \
                    following: "{1}"'.format(sAMAccountName, e.message))
                raise ADException('The password could not be reset due to an unexpected error. Please try again.')

            self.unlock_user(sAMAccountName)
            json_logger('audit', 'NA', 'The user "{0}" had their password reset'.format(sAMAccountName))
            return True
        else:
            json_logger('error', 'NA', 'The distinguished name could not be found for the user \
                "{0}'.format(sAMAccountName))
            raise ADException('The user could not be found in Active Directory. Please try again.')

    def is_account_disabled(self, sAMAccountName):
        """ Returns a boolean based on whether or not the specified account has the flag account disabled
        """
        user_account_control = int(self.get_ldap_attribute(sAMAccountName, 'userAccountControl'))

        if (user_account_control & 2) == 2:
            return True

        return False

    def get_min_password_length(self):
        """ Returns the domain's minimum password length
        """
        return int(self.get_domain_ldap_attribute('minPwdLength'))

    def is_pw_complexity_required(self):
        """ Returns a boolean of whether or not the domain requires password complexity
        """
        return bool(self.get_domain_ldap_attribute('pwdProperties'))

    def match_min_pwd_length(self, password):
        """ Returns a boolean of whether or not the specified password meets the domain's length requirements
        """
        return len(password) >= self.get_min_password_length()

    def match_password_complexity(self, password):
        """ Returns a boolean of whether or not the specified password meets the domain's complexity requirements
        """
        if self.is_pw_complexity_required():
            complexity_score = 0

            # If a capital letter is found in the password
            if search("[A-Z]", password):
                complexity_score += 1
            # If a lowercase letter is found in the password
            if search('[a-z]', password):
                complexity_score += 1
            # If a digit is found in the password
            if search('\d', password):  # pylint: disable=anomalous-backslash-in-string
                complexity_score += 1
            # If a nonletter or number is found in the password (should match any special character)
            if search('\W', password):  # pylint: disable=anomalous-backslash-in-string
                complexity_score += 1

            return complexity_score >= 3
        else:
            return True

    def get_min_pwd_age_in_days(self):
        """ Returns the minimum age a password must be before being changed in days
        """
        min_pwd_age = int(self.get_domain_ldap_attribute('minPwdAge'))
        # Multiply by negative one to make the number positive, then divide by 864000000000 (1 day in file time)
        return (min_pwd_age * -1) / 864000000000

    def sid2str(self, sid):
        """ Converts a hexadecimal string returned from the LDAP query to a
        string version of the SID in format of S-1-5-21-1270288957-3800934213-3019856503-500
        This function was based from: http://www.gossamer-threads.com/lists/apache/bugs/386930
        """
        srl = ord(sid[0])
        number_sub_id = ord(sid[1])
        iav = unpack('!Q', '\x00\x00' + sid[2:8])[0]
        sub_ids = [
            unpack('<I', sid[8+4*i:12+4*i])[0]
            for i in range(number_sub_id)
        ]

        return 'S-{0}-{1}-{2}'.format(srl, iav, '-'.join([str(s) for s in sub_ids]))
