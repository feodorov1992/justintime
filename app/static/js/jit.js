const $ = django.jQuery;
const jQuery = django.jQuery;
let relatedField;
const isHTML = RegExp.prototype.test.bind(/(<([^>]+)>)/i);

$('#hidden_menu').click(function(event) {
    event.stopPropagation();
});

$('#alert>div').click(function(event) {
    event.stopPropagation();
});

$( "#profile_img" ).click(function(event) {
    event.stopPropagation();
    let hiddenMenu = $('#hidden_menu')
    if (hiddenMenu.is(":visible")) {
        hiddenMenu.hide();
        $(this).removeClass('active');
    } else {
        hiddenMenu.show();
        $(this).addClass('active');
    }
    $(this).find('img').each(function () {
        if ($(this).is(":visible")) {
            $(this).hide();
        } else {
            $(this).show();
        }
    })
});

$(window).click(function() {
    if ($('#hidden_menu').is(":visible") && !$('#nav-icon').is(":visible")) {
        $( "#profile_img" ).click()
    }
    if ($('#alert').is(":visible")) {
        $( "#cross" ).click()
    }
});

$('#cross').click( function(){
    $('#alert').removeAttr('style');
    $('#alert_label').html(null);
})

function openModal(content) {
    let container = $('#alert_label')
    let modalWindow = $('#alert')
    container.html(null)
    container.append(content)
    if (!modalWindow.is(":visible")) {
        modalWindow.css('display', 'flex')
    }
    container.find('.django-select2').djangoSelect2()
}

function getModalView(url) {
    $.get(url, function (data) {
        openModal(data)
    })
}

$('.open_mark').click(function () {
    let source = $(this)
    let target = $(source.data('target_id'))
    if (target.is(':visible')) {
        source.removeClass('opened')
        target.hide()
    } else {
        source.addClass('opened')
        target.show()
    }
})


function addForm(template, target) {
    let totalFormsInput = target.find('input[id*="TOTAL_FORMS"]')
    let totalForms = totalFormsInput.val()
    let newForm = template.replaceAll(/__prefix__/g, totalForms)
    let container = target.find('.container').last()
    container.append(newForm)
    $('body').find('.django-select2').djangoSelect2()
    totalForms++
    totalFormsInput.val(totalForms)
}

$('#add_cargo').click(function () {
    addForm(cargoFormTemplate, $('#cargo_formset'))
})

$('#add_quick_doc').click(function () {
    addForm(quickOrderFormTemplate, $('#quick_doc_formset'))
})

function removeForm(elem) {
    let elemID = elem.find('.hidden_fields input').first().val()
    if (!elemID) {
        let totalFormsInput = elem.parents('div[id*="formset"]').first().find('input[id*="TOTAL_FORMS"]')
        let totalForms = totalFormsInput.val()
        totalForms--
        totalFormsInput.val(totalForms)
        elem.remove()
    } else {
        let deleteInput = elem.find('.hidden_fields input[id*="DELETE"]')
        deleteInput.prop('checked')
        elem.hide()
    }
}

$('body').on('click', '.del_btn', function () {
    removeForm($(this).parents('.cargo_form').last())
})

$('body').on('click', 'a', function (event) {
    if ($(this).data('popup') === 'yes') {
        event.preventDefault()
        getModalView($(this).attr('href'))
        relatedField = this.id.slice(7)
    }
})

$('body').on('submit', '#alert_label form', function (event) {
    event.preventDefault();
    $.post(
        this.action,
        $(this).serialize()
    )
        .done(function(data){
            if (isHTML(data)) {
                openModal(data)
            } else {
                data = JSON.parse(data)
                let select = $(`#id_${relatedField}`)
                if (select.find(`option[value='${data.value}']`).length) {
                    select.val(data.value).trigger('change');
                } else {
                    let newOption = new Option(data.obj, data.value, true, true);
                    select.append(newOption).trigger('change');
                }
                $('#cross').click()
            }
        })
})

$('#nav-icon').click(function(){
    $(this).toggleClass('open');
    let menu = $('.menu')
    if (menu.is(':visible')) {
        menu.hide();
    } else {
        menu.show();
    }
});

$('#show-filters').click(function () {
    let filter = $('.filter-form')
    if (!filter.is(':visible')) {
        filter.show()
        $('html').css('overflow', 'hidden');
    }
})

$('#filter-cross').click(function () {
    let filter = $('.filter-form')
    if (filter.is(':visible')) {
        filter.hide()
    }
    $('html').removeAttr('style')
})
