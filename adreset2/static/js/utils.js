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
