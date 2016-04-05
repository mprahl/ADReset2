// Read a page's GET URL variables and return them as an associative array.
// Inspired from http://www.drupalden.co.uk/get-values-from-url-query-string-jquery
function getUrlVars() {
    var vars = [], hash;
    if (window.location.href.indexOf('?') != -1) {
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');

        for (var i = 0; i < hashes.length; i++) {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
    }

    return vars;
}


// Inspired from https://github.com/janl/mustache.js/blob/master/mustache.js
function filterText(text) {
     var entityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    };

    return String(text).replace(/[&<>"'`=\/]/g, function fromEntityMap (s) {
      return entityMap[s];
    });
}


function addStatusMessage(category, message) {

    // Generates a random id for the alert so that the setTimeout function below only applies to that specific alert
    var alertId = Math.floor((Math.random() * 100000) + 1);

    $('#bottomOuterAlertDiv').html('\
        <div id="bottomAlert' + alertId + '" class="alert ' + ((category == 'success') ? 'alert-success' : 'alert-danger') + ' alert-dismissible fade in" role="alert">\
                <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>\
                ' + message + '\
        </div>\
    ').hide().fadeIn();

    setTimeout(function () {
        $('#bottomAlert' + alertId).fadeOut(function() {$(this).remove()}); },
        ((category == 'success') ? 5000 : 8000)
    );
}
