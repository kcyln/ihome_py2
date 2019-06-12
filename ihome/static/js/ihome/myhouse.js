$(document).ready(function(){

    $.get("/api/v1.0/users/auth", function(resp){
        if(resp.errno == "4101"){
            location.href = "/login.html"
        }
        else if (resp.errno == "0"){
            if (resp.data.real_name && resp.data.id_card){               
                $.get("/api/v1.0/user/houses", function(resp){
                    if (resp.errno == "0"){
                        $("#houses-list").html(template("house-list-tmpl", {houses:resp.data.houses}))
                    }else{
                        $("#houses-list").html(template("house-list-tmpl", {houses:[]}))
                    }
                })
            }
        }else{
            $("#houses-list").hide();
            $(".auth-warn").show();
        }
    }, "json")
})