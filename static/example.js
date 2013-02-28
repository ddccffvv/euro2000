function print_today() {
  // ***********************************************
  // AUTHOR: WWW.CGISCRIPT.NET, LLC
  // URL: http://www.cgiscript.net
  // Use the script, just leave this message intact.
  // Download your FREE CGI/Perl Scripts today!
  // ( http://www.cgiscript.net/scripts.htm )
  // ***********************************************
  var now = new Date();
  var months = new Array('jan','feb','mar','april','mei','jun','jul','aug','sep','oct','nov','dec');
  var date = ((now.getDate()<10) ? "0" : "")+ now.getDate();
  function fourdigits(number) {
    return (number < 1000) ? number + 1900 : number;
  }
  var today =  date + " " + months[now.getMonth()] + " " + (fourdigits(now.getYear()));
  return today;
}

// from http://www.mediacollege.com/internet/javascript/number/round.html
function roundNumber(number,decimals) {
  var newString;// The new rounded number
  decimals = Number(decimals);
  if (decimals < 1) {
    newString = (Math.round(number)).toString();
  } else {
    var numString = number.toString();
    if (numString.lastIndexOf(".") == -1) {// If there is no decimal point
      numString += ".";// give it one at the end
    }
    var cutoff = numString.lastIndexOf(".") + decimals;// The point at which to truncate the number
    var d1 = Number(numString.substring(cutoff,cutoff+1));// The value of the last decimal place that we'll end up with
    var d2 = Number(numString.substring(cutoff+1,cutoff+2));// The next decimal, after the last one we want
    if (d2 >= 5) {// Do we need to round up at all? If not, the string will just be truncated
      if (d1 == 9 && cutoff > 0) {// If the last digit is 9, find a new cutoff point
        while (cutoff > 0 && (d1 == 9 || isNaN(d1))) {
          if (d1 != ".") {
            cutoff -= 1;
            d1 = Number(numString.substring(cutoff,cutoff+1));
          } else {
            cutoff -= 1;
          }
        }
      }
      d1 += 1;
    } 
    if (d1 == 10) {
      numString = numString.substring(0, numString.lastIndexOf("."));
      var roundedNum = Number(numString) + 1;
      newString = roundedNum.toString() + '.';
    } else {
      newString = numString.substring(0,cutoff) + d1.toString();
    }
  }
  if (newString.lastIndexOf(".") == -1) {// Do this again, to the new string
    newString += ".";
  }
  var decs = (newString.substring(newString.lastIndexOf(".")+1)).length;
  for(var i=0;i<decimals-decs;i++) newString += "0";
  //var newNumber = Number(newString);// make it a number if you like
  return newString; // Output the result to the form field (change for your purposes)
}

function update_btw() {
    var btw6 = 0;
    var btw0 = 0;
    var btw21 = 0;
    $(".item-row").each(function(i){
       if($(this).find(".btw").val()=="1"){
           temp = $(this).find(".price").html().replace("€", "").replace(",",".");
           if (!isNaN(temp)) btw21 += Number(temp);
       }else if($(this).find(".btw").val()=="2"){
           temp = $(this).find(".price").html().replace("€", "").replace(",",".");
           if (!isNaN(temp)) btw6 += Number(temp);
       }else{
           temp = $(this).find(".price").html().replace("€", "").replace(",",".");
           if (!isNaN(temp)) btw0 += Number(temp);
       }
    });
    
    btw0 = roundNumber(btw0, 2);
    btw6 = roundNumber(btw6, 2);
    btw21 = roundNumber(btw21, 2);
    
    $("#total-0").html("€"+btw0.toString().replace(".",","));
    $("#total-6").html("€"+btw6.toString().replace(".",","));
    $("#total-21").html("€"+btw21.toString().replace(".",","));
    
    $("#netto-0").html("€"+btw0.toString().replace(".", ","));
    
    var b6 = roundNumber(btw6 * .06, 2);
    var b21 = roundNumber(btw21 *.21, 2);
    
    $("#netto-6").html("€"+ roundNumber(btw6-b6, 2).replace(".",","));
    $("#netto-21").html("€"+ roundNumber(btw21-b21, 2).replace(".",","));
    $("#btw-6").html("€"+ b6.toString().replace(".",","));
    $("#btw-21").html("€"+ b21.toString().replace(".",","));
    
    var total = Number(btw0) + Number(btw6) + Number(btw21);
    
    $("#due").html("€"+roundNumber(total, 2).replace(".",","));
    $("#total").html("€"+roundNumber(total, 2).replace(".",","));
    alert(btw0+btw6+btw21);
    
}

function update_total() {
  var total = 0;
  $('.price').each(function(i){
    price = $(this).html().replace("€","").replace(",",".");
    if (!isNaN(price)) total += Number(price);
  });

  total = roundNumber(total,2);

  $('#subtotal').html("€"+total.toString().replace(".",","));
  $('#total').html("€"+total.toString().replace(".",","));
  
  update_balance();
}

function update_balance() {
  var due = $("#total").html().replace("€","").replace(",",".") - $("#paid").val().replace("€","").replace(",",".");
  due = roundNumber(due,2);
  
  $('.due').html("€"+due.toString().replace(".",","));
}

function update_price() {
  var row = $(this).parents('.item-row');
  var price = row.find('.cost').val().replace("€","").replace(",",".") * row.find('.qty').val();
  price = roundNumber(price,2);
  isNaN(price) ? row.find('.price').html("N/A") : row.find('.price').html("€"+price.toString().replace(".",","));
  
  update_btw();
  update_total();
}

function bind() {
  $(".cost").blur(update_price);
  $(".qty").blur(update_price);
}

$(document).ready(function() {

  $('input').click(function(){
    $(this).select();
  });

  $("#paid").blur(update_total);
   
  $("#addrow").click(function(){
    $(".item-row:last").after('<tr class="item-row"><td class="item-name"><div class="delete-wpr"><textarea>Item Name</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td><td class="description"><textarea>Description</textarea></td><td><textarea class="cost">€10</textarea></td><td class="first-row"><textarea class="btw">1</textarea></td><td><textarea class="qty">1</textarea></td><td><span class="price">€10</span></td></tr>');
    if ($(".delete").length > 0) $(".delete").show();
    update_total();
    bind();
  });
  
  bind();
  
  $("tbody").on('click',"tr.item-row td div .delete",function(){
    $(this).parents('.item-row').remove();
    update_total();
    if ($(".delete").length < 2) $(".delete").hide();
  });
  
  $("#date").val(print_today());
  update_total();
  
});
