const saveChanges = () => {
    const table = document.querySelector('table');
    const headers = [];
    const dict = {};

    for (let i = 0; i < table.rows[0].cells.length; i++) {
        headers[i] = table.rows[0].cells[i].innerHTML.toLowerCase().replace(/ /gi, '');
    }

    for (i = 0; i < headers.length; i++) {
        let data = [];
        let header = headers[i];
        for (let j = 1; j <= table.tBodies[0].rows.length; j++) {
            data.push(table.rows[j].cells[i].innerHTML.replace("<br>", "<div>", "</div>", ""));
        }

        dict[header] = data;
   }

    // Send the edited records to the server
    fetch(`/${script_root}/savechanges`, {
        method: "post",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dict)
    })
    .then(resp => {
        //console.log(resp.json());
        return resp.json()
    })
    .then(data => {
        console.log(data);
        alert(data.message);
    })
    .catch(err => {
        console.log(err);
    })
}

