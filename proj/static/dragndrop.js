
/* 
Just a few simple lines of code to stop the default behavior on a drag and drop, 
in order to allow the drag and drop functionality to work
*/

(function(){
    const events = ["drag", "dragstart", "dragend", "dragover", "dragenter", "dragleave", "drop"]
    for (let i = 0; i < events.length; i++){
        document.querySelector('body').addEventListener(events[i], (e) => {
            e.stopPropagation();
            e.preventDefault();
        })
    }

    
    document.querySelector("body").addEventListener('drop', function(event){
        event.stopPropagation();
        event.preventDefault();
        
        const dropped_files = event.dataTransfer.files;
        document.querySelector('#file-submission-form input.form-control-file').files = dropped_files;
        document.querySelector('#file-submission-form').requestSubmit();
    });

})()