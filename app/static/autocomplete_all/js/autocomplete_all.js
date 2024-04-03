function erasePrefix(s, _prefix) {
    if (!_prefix) {
        return s
    }
    return s.substring(_prefix.length + 1)
}

function getPrefix(fieldId, toName=true) {
    if (fieldId.includes('filter')) {
        return ''
    }
    if (toName) {
        fieldId = fieldId.substring(3)
    }
    return fieldId.split('-').slice(0, -1).join('-')
}

function sanitize(string) {  // https://stackoverflow.com/questions/2794137/sanitizing-user-input-before-adding-it-to-the-dom-in-javascript
    if (string === null) {return '';}

    // https://stackoverflow.com/questions/4310535/how-to-convert-anything-to-a-string-safely-in-javascript
    switch (typeof string) {
        case 'object':
            return 'object';
        case 'function':
            return 'function';
        default:
            return string + '';  // to string (dj 3.2 was reported an issue with non-string content here, which fails on string.replace)
    }

    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        "/": '&#x2F;',
    };
    const reg = /[&<>"'/]/ig;
    return string.replace(reg, (match)=>(map[match]));
}

django.jQuery(document).ready(function () {
    window.history.orig_pathname = undefined;
    const select2 = django.jQuery('select.admin-autocomplete')
    select2.on('select2:opening', function (evt) {
        if (!window.history.orig_pathname) {
            window.history.orig_pathname = window.location.pathname + window.location.search;
        }
        let prefix = getPrefix(this.id, false)
        this.modified_location_search_key = '?key=' + erasePrefix(this.id, prefix);
        this.modified_location_search = this.modified_location_search_key + expand_ajax_params(django.jQuery, this.id);
        window.history.replaceState(null, null, window.location.pathname + this.modified_location_search);
    });
    select2.on('select2:closing', function (evt) {
        if (!window.history.orig_pathname) {
            window.history.orig_pathname = window.location.pathname + window.location.search;
        }
        let keypart = (window.location.search + '&').split('&', 1)[0];
        if (keypart === this.modified_location_search_key) {  // opening of new runs earlier of closing the old one :(
            window.history.replaceState(null, null, window.history.orig_pathname);
        }
        let elem = django.jQuery(this)
        if (elem.parents('#grp-filters').length > 0 || elem.parents('#changelist-filter').length > 0) {
            let val = django.jQuery(this).val() || '';
            let class_name = this.className;
            let param = this.name;
            if (class_name.includes('admin-autocomplete'))
            {
                window.location.search = search_replace(param, val);
            }
        }
    });
});

const prohibitedNames = [
    'csrfmiddlewaretoken', 'action'
]

function expand_ajax_params($, fieldId) {

    function make_addition(name, value, firstChar = '&') {
       return firstChar + erasePrefix(name, prefix) + '=' + sanitize(value)
    }

    function getFilteredJQuery(query, prefix) {
        return $(query).filter(function(){
            let elem = $(this)
            let name = elem.attr('name')

            if (!name) {
                return false
            }

            let notInExclude = prohibitedNames.indexOf(name) === -1
            let notIsButton = !name.startsWith('_')
            let checkPrefix
            if (!prefix) {
                checkPrefix = !name.includes('-')
            } else {
                checkPrefix = name.startsWith(prefix)
            }
            return notInExclude && checkPrefix && notIsButton
        })
    }

    let expanded = '';
    const prefix = getPrefix(fieldId);
    let controls = getFilteredJQuery('input, select', prefix)

    controls.each(function () {
        let obj = $(this);
        if (obj.prop('type') === 'checkbox') {
            expanded += make_addition(obj.prop('name'), obj.prop('checked'))
        } else {
            expanded += make_addition(obj.prop('name'), obj.val())
        }
    })

    let textareas = getFilteredJQuery('textarea', prefix)
    textareas.each(function () {
        let obj = $(this);
        let content = obj.val();
        expanded += make_addition(obj.prop('name'), content.length.toString())
        if (content.length <= 40) {
            expanded += ':' + sanitize(content);
        }
    })
    return expanded;
}
