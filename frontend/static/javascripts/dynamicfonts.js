    $(function() {
        var len_fit = 10; // According to your question, 10 letters cat fit in.
        var un = $('#datapoint');

        // Get the lenght of user name.
        var len_user_name = un.html().length;
        if(len_fit < len_user_name ){

            // Calculate the new font size.
            var size_now = parseInt(un.css("font-size"));
            var size_new = size_now * len_fit/len_user_name;

            // Set the new font size to the user name.
            un.css("font-size",size_new); 
        }
    });