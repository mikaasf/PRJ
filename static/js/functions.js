// page.html

function startRecording() {
    if (document.getElementById("changeRec").innerHTML === "Stop &amp; save recording") {
        isRecording = false;
        let form = document.createElement("form");
        form.setAttribute("method", "post");
        let container = document.getElementById("video_controls");
        let elements = [container.childElementCount];
        let j = 0;
        while (container.hasChildNodes()) {
            elements[j] = (container.removeChild(container.lastChild));
            j++;
        }
        for (let i = 0; i < elements.length; i++) {
            form.appendChild(elements[i]);
            console.log(elements[i]);
        }
        document.getElementById("video_controls").appendChild(form);
        return;
    }

    isRecording = true;
    startingTime = new Date().getTime() / 1000;
    let rec_light = document.getElementById("rec");
    rec_light.classList.toggle("Rec");
    let rec_button = document.getElementById("changeRec");
    rec_button.classList.toggle("btn-danger");
    document.getElementById("changeRec").innerHTML = "Stop & save recording";
}

// annotations.html

function toggleButton(element) {
    let emotionButtons = document.querySelectorAll(".emoticons");
    // Check to see if the button is pressed
    let pressed = (element.getAttribute("aria-pressed") === "true");
    console.log(pressed);
    if (pressed) {
        console.log("unselected " + element.id);
        element.parentElement.style.background = "";
        if (vid == null) {
            counter = new Date().getTime() / 1000 - startingTime - emotionTimer;
        }
        if (counter < emotionTimer) {
            let temp = counter;
            counter = emotionTimer;
            emotionTimer = temp;
        }
        socket.emit('emotionButton', {
            type: $(element).attr('id'),
            frameID: emotionTimer,
            duration: counter - emotionTimer
        });
        console.log(newID);
        addAnnotationToList([element.id, {'id': newID}, emotionTimer, counter], true);
    } else {
        for (let i = 0; i < emotionButtons.length; i++) {
            if (emotionButtons.item(i) !== element)
                console.log("unpressed " + emotionButtons.item(i).id);
            if (emotionButtons.item(i).getAttribute("aria-pressed") === "true") {
                emotionButtons.item(i).parentElement.style.background = "";
                emotionButtons.item(i).setAttribute("aria-pressed", "false");
            }
        }
        if (vid != null) {
            emotionTimer = vid.currentTime;
        } else {
            emotionTimer = new Date().getTime() / 1000 - startingTime;
        }
        element.parentElement.style.background = "greenyellow";

    }
    // Change aria-pressed of the selected button to the opposite state
    element.setAttribute("aria-pressed", !pressed + "");
    console.log("clicked " + element.id);
}

function formatTimeHHMMSS(time) {
    let sec_num = parseInt(time, 10);
    let minutes = Math.floor(sec_num / 60);
    let seconds = sec_num - (minutes * 60);

    if (minutes < 10) {
        minutes = "0" + minutes;
    }
    if (seconds < 10) {
        seconds = "0" + seconds;
    }
    return minutes + ':' + seconds;
}

function formatToSeconds(time) {
    let array_time = time.split(":");
    return (+array_time[0]) * 60 + (+array_time[1]);
}

function addAnnotationToList(annotation, newAnnot) {
    let background_color_emotions = "lightgoldenrodyellow";
    let background_color_others = "powderblue";
    let background;
    socket.emit("ask for id");
    if (annotation[0] === "happy" || annotation[0] === "sad" || annotation[0] === "surprised" || annotation[0] === "afraid" || annotation[0] === "angry" || annotation[0] === "disgusted") {
        background = background_color_emotions;
    } else {
        background = background_color_others
    }
    let defaultTime = 5;
    let duration;
    if (annotation[3] === null)
        duration = parseFloat(annotation[2]) + defaultTime;
    else
        duration = parseFloat(annotation[2]) + parseFloat(annotation[3]);

    ids_time[annotation[1]['id']] = [parseFloat(annotation[2]), duration];

    duration = formatTimeHHMMSS(duration);
    annotation[2] = formatTimeHHMMSS(annotation[2]);

    let button_edit = "<button title='Edit Annotation' onclick='editAnnot(this)' id=\"" + "edit_" + annotation[1]['id'] + "\" class=\"edit_ann\">✎</button>";
    let button_del = "<button title='Remove Annotation' onclick='deleteAnnot(this)' id=\"" + "del_" + annotation[1]['id'] + "\" class=\"delete_ann\">x</button>";
    let annot_html = '<input style="background: ' + background + '; color: #222222" type="text" disabled value="' + annotation[0] + '"><span style="float: right"><small><input disabled value="' + annotation[2] + '" style="background: ' + background + '; color: #222222">' + ' &rbarr; ' + '<input disabled value="' + duration + '" style="background: ' + background + '; color: #222222"></small>'
    $('#annotations_list').prepend('<li class="list-group-item" style="background: ' + background + ';" id="ann_' + annotation[1]['id'] + '">' + annot_html + button_edit + button_del + '</span></li>');
    if (newAnnot)
        unsavedChanges();

}

function editAnnot(btn) {
    if (btn.parentNode.parentNode.childNodes.item(0).disabled) {
        btn.parentNode.parentNode.childNodes.item(0).disabled = false;
        btn.parentNode.childNodes.item(0).childNodes.item(0).disabled = false;
        btn.parentNode.childNodes.item(0).childNodes.item(2).disabled = false;
        btn.innerHTML = "Save &check;"
        return;
    }
    console.log("edited ")
    socket.emit('editAnnotation', {
        idAnnotation: btn.getAttribute('id').split("_")[1],
        newValue: btn.parentNode.parentNode.childNodes.item(0).value,
        newInitFrame: formatToSeconds(btn.parentNode.childNodes.item(0).childNodes.item(0).value),
        newDuration: formatToSeconds(btn.parentNode.childNodes.item(0).childNodes.item(2).value)
    });
    btn.parentNode.parentNode.childNodes.item(0).disabled = true;
    btn.parentNode.childNodes.item(0).childNodes.item(0).disabled = true;
    btn.parentNode.childNodes.item(0).childNodes.item(2).disabled = true;
    btn.innerHTML = "✎";
    unsavedChanges();
}

function deleteAnnot(btn) {
    console.log("deleting " + btn.getAttribute('id'));
    socket.emit('deleteAnnotation', {
        idAnnotation: btn.getAttribute('id').split("_")[1]
    });
    document.getElementById("annotations_list").removeChild(btn.parentNode.parentNode)
    unsavedChanges();
}

function saveChanges() {
    socket.emit('saveChanges');
    noChanges = true;
}

function unsavedChanges() {
    noChanges = false;
    document.getElementById("err_log").innerHTML = "You have unsaved annotations, please save changes before leaving.";
    document.getElementById("saveChanges").disabled = false;
}

function callDeepface() {
    if (noChanges) {
        document.getElementById("loaderImg").style.display = "inline";
        socket.emit("deepface_start");
        document.getElementById("deepface_generate").disabled = true;

    } else {
        alert("Please save your changes before auto analysing emotions");
    }
}

//login.html and signup.html

function hide_error() {
    document.getElementById("error").style.visibility = "hidden";
}

