(function(){
    finalSubmitButton = document.getElementById("final-submit-button");

    finalSubmitButton.addEventListener("click", async function(){
        if (!confirm("Are you sure you want to submit this data to the database?")){
            return
        }
        const response = await fetch(`/${script_root}/load`, {method: 'post'});
        console.log(response);
        const result = await response.json();
        console.log(result);

        alert(result.user_notification);

        window.location = `/${script_root}`;

    })

    
})()