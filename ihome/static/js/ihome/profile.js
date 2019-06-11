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
    $("#form-avatar").submit(function(e){
        // 阻止表单的默认行为
        e.preventDefault();
        // 利用jquery.form.min.js提供的ajaxSubmit对表单进行异步提交
        $(this).ajaxSubmit({
            url: "/api/v1.0/users/avatar",
            type: "post",
            dataType: "json",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            success: function(resp){
                if (resp.errno == "0"){
                    // 上传成功
                    var avatar_url = resp.data.avatar_url;
                    $("#user-avatar").attr("src", avatar_url);
                }else{
                    alert(resp.errmsg)
                }
            }
        })
    });
    $("#form-name").submit(function(e){
        // 阻止表单的默认行为
        e.preventDefault();
        var username = $("#user-name").val()
        if (!username){
            alert("请填写用户名！")
            return;
        }
        var req_data = {"username": username}
        var req_json = JSON.stringify(req_data)
        $.ajax({
            url: "/api/v1.0/users/username", 
            type: "put",
            data: req_json,
            contentType: "application/json",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },//　请求头，讲csrf_token值放到请求中，方便后端csrf进行验证
            success: function(resp){
                if (resp.errno == "0"){
                    showSuccessMsg()
                }else if(resp.errno == "4101"){
                    location.href = "/login.html"
                }else{
                    alert(resp.errmsg)
                }
            }
        })
    })
})