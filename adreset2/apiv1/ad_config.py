"""
Author: StackFocus
File: configs.py
Purpose: The configs API for ADReset2 which allows an admin to update PostMaster configurations
"""
from flask import request
from flask_login import login_required, current_user
from adreset2 import db
from adreset2.models import AdConfigs
from adreset2.errors import ValidationError, GenericError
from adreset2.decorators import json_wrap, paginate
from adreset2.apiv1 import apiv1
# This broad import statement is so that functions from utils can be mocked in the Blueprint
import adreset2.utils


@apiv1.route('/ad_config', methods=['GET'])
@login_required
@paginate()
def ad_config():
    return AdConfigs.query


@apiv1.route('/ad_config', methods=['POST'])
@login_required
@json_wrap
def set_ad_config():
    """ Sets the AD configuration settings and returns HTTP 200 on success
    """
    json = request.get_json(force=True)
    for required_param in ['domain_controller', 'port', 'domain', 'username', 'password']:
        if required_param not in json or not json[required_param]:
            raise ValidationError('The "{0}" parameter was not supplied'.format(required_param))

    if adreset2.utils.try_ad_connection(json['domain_controller'], json['port'], json['domain'],
                                        json['username'], json['password']):

        for setting in json:
            db.session.add(AdConfigs().from_key_pair(setting, json[setting]))

        try:
            db.session.commit()
            adreset2.utils.json_logger('audit', current_user.username, 'The Active Directory configuration was updated successfully')
        except ValidationError as e:
            raise e
        except Exception as e:
            db.session.rollback()
            adreset2.utils.json_logger(
                'error', current_user.username,
                'The following error occurred in update_config: {0}'.format(str(
                    e)))
            raise GenericError('The configuration could not be updated')
        finally:
            db.session.close()

        return {}, 201
