const $ = django.jQuery;
const jQuery = django.jQuery;

$('#hidden_menu').click(function(event) {
    event.stopPropagation();
});

$('#alert').click(function(event) {
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
    if ($('#hidden_menu').is(":visible")) {
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

function getModalView(url) {
    $.get(url, function (data) {
        $('#alert_label').html(data)
        $('#alert').css('display', 'flex')
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
