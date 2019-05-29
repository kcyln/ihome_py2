function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout() {
    $.ajax({
        url: "/api/v1.0/session", 
        type: "delete",
        headers: {"X-CSRFToken": getCookie("csrf_token")},
        dataType: "json",
        success: function(resp){
        if (resp.errno == "0") {
            location.href = "/index.html";
        }}
    })
}

$(document).ready(function(){
    $.get("/api/v1.0/users/profile", function(resp){
        if(resp.errno == "4101"){
            location.href = "/login.html"
        }
        else if (resp.errno == "0"){
            $("#user-name").html(resp.data.name)
            $("#user-mobile").html(resp.data.mobile)
            $("#user-avatar").attr("src", resp.data.avatar)
        }else{
            alert(resp.errmsg)
        }
    }, "json")
})