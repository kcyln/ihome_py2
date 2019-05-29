function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(document).ready(function(){

    $.get("/api/v1.0/users/auth", function(resp){
        if(resp.errno == "4101"){
            location.href = "/login.html"
        }
        else if (resp.errno == "0"){
            if (resp.data.real_name && resp.data.id_card){
                // $("#form-auth").hide()
                $("#real-name").val(resp.data.real_name)
                $("#id-card").val(resp.data.id_card)
                //　给input添加disable属性，禁止用户修改
                $("#real-name").prop("disabled", true)
                $("#id-card").prop("disabled", true)
                // 隐藏提交按钮
                $(".btn-success").hide()  
            }
        }else{
            // $(".menu-text").hide()
            alert(resp.errmsg)
        }
    }, "json")

    // $(".fr").click(function(){
    //     $(".menu-text").hide()
    //     $("#form-auth").show()
    // })

    $("#form-auth").submit(function(e){
        // 阻止表单的默认行为
        e.preventDefault();
        var realName = $("#real-name").val()
        var idCard = $("#id-card").val()
        if (realName == "" || idCard == ""){
            $(".error-msg").show()
        }
        var req_data = {"real_name": realName, "id_card": idCard}
        var req_json = JSON.stringify(req_data)
        $.ajax({
            url: "/api/v1.0/users/auth", 
            type: "post",
            data: req_json,
            contentType: "application/json",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },//　请求头，讲csrf_token值放到请求中，方便后端csrf进行验证
            success: function(resp){
                if (resp.errno == "0"){
                    $(".error-msg").hide()
                    showSuccessMsg()
                    //　给input添加disable属性，禁止用户修改
                    $("#real-name").prop("disabled", true)
                    $("#id-card").prop("disabled", true)
                    // 隐藏提交按钮
                    $(".btn-success").hide() 
                }else{
                    // $(".error-msg").show()
                    alert(resp.errmsg)
                }
            }
        })
    })
})