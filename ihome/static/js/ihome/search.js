var cur_page=1;
var next_page=1;
var total_page=1;
var house_data_querying=true;  // 是否正在向后台获取数据


function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function updateFilterDateDisplay() {
    var startDate = $("#start-date").val();
    var endDate = $("#end-date").val();
    var $filterDateTitle = $(".filter-title-bar>.filter-title").eq(0).children("span").eq(0);
    if (startDate) {
        var text = startDate.substr(5) + "/" + endDate.substr(5);
        $filterDateTitle.html(text);
    } else {
        $filterDateTitle.html("入住日期");
    }
}

// 更新房源列表信息
// action表示从后端请求的数据在前端的展示方式
// 默认采用追加方式
// action=renew　代表页面数据清空从新展示
function updateHouseData(action){
    var areaId = $(".filter-area li.active").attr("area-id");
    if (undefined == areaId) {areaId = "";}
    var startDate = $("#start-date").val();
    var endDate = $("#end-date").val();
    var sortKey = $(".filter-sort li.active").attr("sort-key");
    var params = {
        aid: areaId,
        start_date: startDate,
        end_date: endDate,
        sort_key: sortKey,
        page: next_page
    }
    $.get("/api/v1.0/houses", params, function(resp){
        house_data_querying = false;
        
        if (resp.errno == "0"){
            if (resp.data.total_page == 0){
                $(".house-list").html("暂时没有符合您查询的房屋信息")
            }else{
                total_page = resp.data.total_page;
                if(action == "renew"){
                    cur_page = 1;
                    $(".house-list").html(template("house-list-tmpl", {houses:resp.data.houses}))
                }else{
                    cur_page = next_page;
                    $(".house-list").append(template("house-list-tmpl", {houses:resp.data.houses}))
                }
            }
        }
    })
}


$(document).ready(function(){
    var queryData = decodeQuery();
    var startDate = queryData["startDate"];
    var endDate = queryData["endDate"];
    $("#start-date").val(startDate); 
    $("#end-date").val(endDate); 
    updateFilterDateDisplay();
    var areaName = queryData["aname"];
    if (!areaName) areaName = "位置区域";
    $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html(areaName);

    // 获取筛选条件中的城市区域信息
    $.get("/api/v1.0/areas", function(data){
        if (data.errno == "0"){
            var areaId = queryData["aid"]
            if (areaId){
                // 遍历从后端获取的城区信息，添加到页面中
                for (var i=0; i<data.data.length; i++){
                    // 对于从url查询字符串参数拿到的城区，在页面中坐高亮展示
                    // 后端获取到的城区id是整型，从url参数中获取到的是字符串，所以将url中获取的转换为整型
                    areaId = parseInt(areaId);
                    if (data.data[i].aid == areaId){
                        $(".filter-area").append('<li area-id="'+data.data[i].aid+'" class="active">'+data.data[i].aname+'</li>')
                    }else{
                        $(".filter-area").append('<li area-id="'+data.data[i].aid+'">'+data.data[i].aname+'</li>')
                    }
                }
            }else{
                for (var i=0; i<data.data.length; i++){
                    $(".filter-area").append('<li area-id="'+data.data[i].aid+'">'+data.data[i].aname+'</li>')
                }
            }
            // 在页面添加好城区选项信息后，更新展示房屋列表信息
            updateHouseData("renew");
            // 获取页面显示窗口的高度
            var windowHeight = $(window).height();
            // 为窗口的滚动添加事件函数
            window.onscroll=function(){
                var b = document.documentElement.scrollTop==0?document.body.scrollTop:document.body.clientTop
                var c = document.documentElement.scrollTop==0?document.body.scrollHeight:document.body.clientHeight
                // 如果滚动到接近窗口底部
                if(c-b<windowHeight+50){
                    // 如果没有正在向后端发送查询房屋列表信息的请求
                    if(!house_data_querying){
                        house_data_querying=true;
                        if(cur_page<total_page){
                            next_page = cur_page +1
                            updateHouseData();                        
                        }else{
                            house_data_querying=false
                        }
                    }
                }

            }
        }
    })

    

    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    var $filterItem = $(".filter-item-bar>.filter-item");
    $(".filter-title-bar").on("click", ".filter-title", function(e){
        var index = $(this).index();
        if (!$filterItem.eq(index).hasClass("active")) {
            $(this).children("span").children("i").removeClass("fa-angle-down").addClass("fa-angle-up");
            $(this).siblings(".filter-title").children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).addClass("active").siblings(".filter-item").removeClass("active");
            $(".display-mask").show();
        } else {
            $(this).children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).removeClass('active');
            $(".display-mask").hide();
            updateFilterDateDisplay();
        }
    });
    $(".display-mask").on("click", function(e) {
        $(this).hide();
        $filterItem.removeClass('active');
        updateFilterDateDisplay();
        cur_page=1;
        next_page=1;
        total_page=1;
        updateHouseData("renew")

    });
    $(".filter-item-bar>.filter-area").on("click", "li", function(e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html($(this).html());
        } else {
            $(this).removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html("位置区域");
        }
    });
    $(".filter-item-bar>.filter-sort").on("click", "li", function(e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(2).children("span").eq(0).html($(this).html());
        }
    })
})