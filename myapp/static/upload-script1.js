$('#fileup').change(function () {
    var res = $('#fileup').val();
    var arr = res.split('\\');
    var filename = arr.slice(-1)[0];
    filextension = filename.split('.');
    filext = '.' + filextension.slice(-1)[0];
    valid = ['.csv'];

    if (valid.indexOf(filext.toLowerCase()) == -1) {
        // File extension is not valid
        $('.imgupload').hide('slow');
        $('.imgupload.ok').hide('slow');
        $('.imgupload.stop').show('slow');

        $('#namefile').css({ color: 'red', 'font-weight': 700 });
        $('#namefile').html("Le format de fichier " + filename + " n'est pas CSV !");

        $('#submitbtn').hide();
        $('#fakebtn').show();
    } else {
        // File extension is valid
        $('.imgupload').hide('slow');
        $('.imgupload.stop').hide('slow');
        $('.imgupload.ok').show('slow');

        $('#namefile').css({ color: 'green', 'font-weight': 700 });
        $('#namefile').html(filename);

        $('#submitbtn').show();
        $('#fakebtn').hide();
    }
});