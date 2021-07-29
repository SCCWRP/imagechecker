const script_root = 'imagechecker';

function enterUnfocus(event, cell) { 
    var code = (event.keyCode ? event.keyCode : event.which);
    if (code == 13) {
       cell.blur();
    }
 }