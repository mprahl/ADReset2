"use strict";
var _domain_controller = null,
    _port = null,
    _domain = null,
    _username = null,
    _password = null,
    _configPanelButtonDiv = null;


function initializeVars() {
    _domain_controller = $('#inputDomainController');
    _port = $('#inputPort');
    _domain = $('#inputDomainName');
    _username = $('#inputUsername');
    _password = $('#inputPassword');
    _configPanelButtonDiv = $('#configPanelButtonDiv button[type=submit]');
}


function applyFormError(element) {
    element.parent().addClass('has-error');
    element.focus();
    _configPanelButtonDiv.button('reset');
}


function removeFormErrors() {
    // Remove any error bordering on the input fields
    _domain_controller.parent().removeClass('has-error');
    _port.parent().removeClass('has-error');
    _domain.parent().removeClass('has-error');
    _username.parent().removeClass('has-error');
    _password.parent().removeClass('has-error');
}


function setAdConnectionSettings(domain_controller, port, domain, username, password) {

    $.ajax({
        url: '/api/v1/ad_config',
        type: 'post',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
            'domain_controller': domain_controller,
            'port': port,
            'domain': domain,
            'username': username,
            'password': password
        }),

        success: function (response) {
            _password.val('');
            _configPanelButtonDiv.button('reset');
            addStatusMessage('success', 'The connection settings were updated successfully');
        },

        error: function (response) {
            _configPanelButtonDiv.button('reset');
            addStatusMessage('error', filterText(jQuery.parseJSON(response.responseText).message));
        }
    });
}


function getAdConnectionSettings() {

    $.getJSON('/api/v1/ad_config', function (result) {
        $.each(result['items'], function (j, item) {
            if (item['setting'] === 'domain_controller') {
                _domain_controller.val(item['value']);
            }
            else if (item['setting'] === 'port') {
                _port.val(item['value']);
            }
            else if (item['setting'] === 'domain') {
                _domain.val(item['value']);
            }
            else if (item['setting'] === 'username') {
                _username.val(item['value']);
            }
        });
    })
    .fail(function (jqxhr, textStatus, error) {
        addStatusMessage('error', 'An error occurred when retrieving the current settings');
    });
}


function adConnectionSettingsListeners() {
    _configPanelButtonDiv.unbind();
    _configPanelButtonDiv.on('click', function (event) {

        removeFormErrors();
        $(this).button('loading');
        // If _domain_controller is empty, highlight it in red
        if (!_domain_controller.val()) {
            applyFormError(_domain_controller);
        }
        else if (!_port.val()) {
            applyFormError(_port);
        }
        else if (!_domain.val()) {
            applyFormError(_domain);
        }
        else if (!_username.val()) {
            applyFormError(_username);
        }
        else if (!_password.val()) {
            applyFormError(_password);
        }
        else {
            removeFormErrors();
            // Update the Connection Settings
            setAdConnectionSettings(_domain_controller.val(), _port.val(), _domain.val(), _username.val(), _password.val());
        }
        event.preventDefault();
    });

    $('[data-toggle="tooltip"]').tooltip();
}


$(document).ready(function () {
    initializeVars();
    getAdConnectionSettings();
    adConnectionSettingsListeners();
});
