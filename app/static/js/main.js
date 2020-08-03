$(document).ready(function(){
    $(".dropdown, .btn-group").hover(function(){
        var dropdownMenu = $(this).children(".dropdown-menu");
        if(dropdownMenu.is(":visible")){
            dropdownMenu.parent().toggleClass("open");
        }
    });
});

function add_to_cart(id) {
    quantity = $("#q"+id).val();
    if($.isNumeric(quantity) == true){
        if($('#check'+id).is(":checked")){
            checkbox = "checked"
        }
        else {
            checkbox = "unchecked"
        }
        $.ajax({
            type: "POST",
            url: "/add_to_cart",
            data: {id: id, quantity: quantity, checkbox: checkbox},
            dataType: "json",
            success: function(data){
                $("#q"+id).val('');
                $("#cart-total").text(data.total)
                $('#check'+id).prop("checked", false);
                document.getElementById(id).className = "fa fa-heart-o";
            }
        });
    }
    else {
        $("#error"+id).text("Please enter desire quantity in digit.");
    }
}

function remove_cart_item(id, quantity, price) {
    $.ajax({
        type: "DELETE",
        url: "/remove_cart_item",
        data: {id: id, quantity: quantity, price: price},
        dataType: "json",
        success: function(data){
            total = $('#totalprice').text();
            total = parseInt(total) - parseInt(data.tprice);
            $('#totalprice').text(total);
            $("#cart-total").text(data.total);
            $("#tr"+id).fadeOut();
        }
    });
}

function goBack() {
    window.history.back();
}

function tabImage(imgs) {
    var expandImg = document.getElementById("expandedImg");
    expandImg.src = imgs.src;
    expandImg.parentElement.style.display = "block";
}

function viewProduct(id) {
    window.location.assign("/product_detail/"+id);
}

function heart(id) {
    document.getElementById("check"+id).checked = true;
    document.getElementById(id).className = "fa fa-heart fa-2x";
}

function delete_product(id) {
    $.ajax({
        type: "DELETE",
        url: "/delete_from_db",
        data: {id: id},
        dataType: "json",
        success: function(){
            $("#tr"+id).fadeOut();
        },
        error: function(){
            alert("Error!");
        }
    });
}