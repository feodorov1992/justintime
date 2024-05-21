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
