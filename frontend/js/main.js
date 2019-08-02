
(function ($) {
    "use strict";

    /*==================================================================
    [ Validate ]*/
    var input = $('.validate-input .input100');
    var tdna = new TypingDNA();
    tdna.start();

    $('.validate-form').on('submit',function(e){
        e.preventDefault();

        for(var i=0; i<input.length; i++) {
            if(validate(input[i]) == false){
                showValidate(input[i]);
                return false;
            }
        }

        $('#login').click();
    });

    $('.validate-form .input100').each(function(){
        $(this).focus(function(){
           hideValidate(this);
        });
    });

    $('.login100-form-btn').click(function(){
        console.log($('#email').val());
        console.log($('#password').val());
    });

    function validate (input) {
        if($(input).attr('type') == 'email' || $(input).attr('name') == 'email') {
            if($(input).val().trim().match(/^([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{1,5}|[0-9]{1,3})(\]?)$/) == null) {
                return false;
            }
        }
        else {
            if($(input).val().trim() == ''){
                return false;
            }
        }
    }

    function showValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function hideValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    function setMessage(text, acc) {
        $('#message').text(text);

        if (typeof acc !== 'undefined'){
            $(".circle-wrap .circle .mask.full, .circle-wrap .circle .fill").css("transform", "rotate("+ acc*180 +"deg)");
            $("#percent").text("" + Math.round(acc*100) + "%")
        }
    }

    $('#login').click(function (e){
        e.preventDefault();
        tdna.stop();
        var email = $('#email').val();
        var emailPattern = tdna.getTypingPattern({type:2,  targetId:"email"});
        var passwordPattern = tdna.getTypingPattern({type:2, targetId:"password"});

        $.ajax({
            type: 'POST',
            url: 'http://192.168.31.240:5000/predict',
            data: JSON.stringify ({email: email, keystroke: passwordPattern}), // or JSON.stringify ({name: 'jonas'}),
            success: function(data) { setMessage(data.msg, data.acc); },
            error: console.log,
            contentType: "application/json",
            dataType: 'json'
        });
        console.log(emailPattern);
        console.log(passwordPattern);
    })

    $('#register').click(function (e){
        e.preventDefault();
        tdna.stop();
        var email = $('#email').val();
        var emailPattern = tdna.getTypingPattern({type:2,  targetId:"email"});
        var passwordPattern = tdna.getTypingPattern({type:2, targetId:"password"});

        $.ajax({
            type: 'POST',
            url: 'http://192.168.31.240:5000/addData',
            data: JSON.stringify ({email: email, keystroke: passwordPattern}), // or JSON.stringify ({name: 'jonas'}),
            success: function(data) { setMessage(data.msg); },
            error: console.log,
            contentType: "application/json",
            dataType: 'json'
        });
        console.log(emailPattern);
        console.log(passwordPattern);
        $('#password').val("");
        $('#message').css('visibility', 'visible');
    })

    $('#reset').click(function (e) {
        tdna.reset();
        tdna.start();
        setMessage("")
        $('#password').val("");
    })

})(jQuery);
