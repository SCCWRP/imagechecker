(function(){
    fileForm = document.getElementById("file-submission-form");
    loginForm = document.getElementById("login-form");

    loginForm.addEventListener("submit", async (e) => {
        e.stopPropagation();
        e.preventDefault();
        const formData = new FormData();
        formData.append('login_email', document.querySelector('#login_email').value);
        const response = await fetch(`/${script_root}/login`, {
            method: 'post',
            body: formData
        });
        const result = await response.json();
        console.log(result);
        document.querySelector('#login-form-container').classList.add('hidden');
        document.querySelector('#file-submit-form-container').classList.remove('hidden');
    })
    
    

    // routine for submitting the file(s)
    fileForm.addEventListener("submit", async function(e) {
        
        e.stopPropagation();
        e.preventDefault();

        // an example of how we can put a loader gif
        //document.querySelector(".records-display-inner-container").innerHTML = '<img src="/changerequest/static/loading.gif">';
        
        const dropped_files = document.querySelector('[type=file]').files;
        const attempt_measurement = document.querySelector("#attempt_measurement").checked;
        const formData = new FormData();
        for(let i = 0; i < dropped_files.length; ++i){
            /* submit as array to as file array - otherwise will fail */
            formData.append('files[]', dropped_files[i]);
        }
        formData.append('measure', attempt_measurement)

        const response = await fetch(`/${script_root}/upload`, {
            method: 'post',
            body: formData
        });
        document.querySelector(".before-submit").classList.add("hidden");
        document.querySelector(".after-submit").classList.remove("hidden");
        console.log(response);
        const result = await response.json();
        console.log(result);

        if (Object.keys(result).includes("errs")) {
            if (result['errs'].length == 0){
                document.querySelector(".final-submit-button-container").classList.remove("hidden");
            }
        }
        
        window.location = `/${script_root}/report`;
        
        // we can possibly validate the email address on the python side and return a message in "result"
        // and handle the situation accordingly
        //document.querySelector(".file-form-container").classList.add("hidden");

    })

  

})()