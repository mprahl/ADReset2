"""
Author: StackFocus
File: views.py
Purpose: contains the views of the application
"""

from flask import render_template, redirect, request, flash, url_for
from jinja2 import evalcontextfilter, Markup, escape
from flask_login import login_user, logout_user, login_required, current_user
from adreset2 import app, login_manager, models
from adreset2.forms import LoginForm
from adreset2.utils import get_wtforms_errors, json_logger


@app.template_filter()
@evalcontextfilter
def new_line_to_break(eval_ctx, value):
    """ Jinja2 filter to convert all \n to <br> while escaping the text
    """
    result = ''
    for i, line in enumerate(value.split('\n')):
        if i != 0:
            result += '<br>'
        result += str(escape(line))

    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@login_manager.user_loader
def user_loader(user_id):
    """ Function to return user for login
    """
    return models.Admins.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized_callback():
    """ Function to redirect after logging in when prompted for login
    """
    return redirect('/login?next=' + request.path)


@login_required
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', title='ADReset2 Dashboard', authenticated=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm.new()

    if request.method == 'GET':
        return render_template('login.html', title='ADReset2 Login', login_form=login_form)
    elif login_form.validate_on_submit():
        login_user(login_form.admin, remember=False)
        json_logger(
            'auth', login_form.admin.username,
            'The administrator "{0}" logged in successfully'.format(
                login_form.admin.username))
        return redirect(request.args.get('next') or url_for('index'))
    else:
        wtforms_errors = get_wtforms_errors(login_form)
        if wtforms_errors:
            flash(wtforms_errors)

    return redirect(url_for('login'))


@app.route('/logout', methods=["GET"])
def logout():
    """ Logs out the current user
    """
    if current_user.is_authenticated:
        logout_user()
        flash('Successfully logged out', 'success')

    return redirect(url_for('login'))


@app.route('/configs', methods=['GET'])
@login_required
def configs_ui():
    """ Displays the app's configurations
    """
    return render_template('configs.html', title='ADReset2 App Configuration',
                           authenticated=current_user.is_authenticated)


@app.route('/ad_config', methods=['GET'])
@login_required
def ad_config_ui():
    """ Displays the app's configurations
    """
    return render_template('ad_config.html', title='ADReset2 Active Directory Configuration',
                           authenticated=current_user.is_authenticated)

