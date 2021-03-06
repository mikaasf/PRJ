// page.html

function timeToString(time) {
    let diffInHours = time / 3600000;
    let hh = Math.floor(diffInHours);

    let diffInMin = (diffInHours - hh) * 60;
    let mm = Math.floor(diffInMin);

    let diffInSec = (diffInMin - mm) * 60;
    let ss = Math.floor(diffInSec);

    let formattedHH = hh.toString().padStart(2, "0");
    let formattedMM = mm.toString().padStart(2, "0");
    let formattedSS = ss.toString().padStart(2, "0");

    return `${formattedHH}:${formattedMM}:${formattedSS}`;
}

// let startTime;
// let elapsedTime = 0;
// let timerInterval;

function print(txt) {
    document.getElementById("timer").innerHTML = txt;
}

function start() {
    startTime = Date.now() - elapsedTime;
    timerInterval = setInterval(function printTime() {
      elapsedTime = Date.now() - startTime;
      print(timeToString(elapsedTime));
    }, 10);
}

function camOff(videoElem) {
    videoElem.src = "static/imgs/no_cam.jpg";
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
        if (vid === undefined) {
            counter = new Date().getTime() - recordTimer - emotionTimer;
        }
        if (counter < emotionTimer) {
            let temp = counter;
            counter = emotionTimer;
            emotionTimer = temp;
        }
        let duration = counter - emotionTimer;

        if (vid === undefined) {
            duration = (new Date().getTime()) - recordTimer - annotationLeftTimeStamp;

            annotationLeftTimeStamp = annotationLeftTimeStamp / 1000;
            duration = duration / 1000;

        } else if (vid !== undefined) {
            annotationLeftTimeStamp = emotionTimer;
        }

        socket.emit('emotionButton', {
            type: $(element).attr('id'),
            frameID: annotationLeftTimeStamp,
            duration: duration
        });

        console.log(newID);
        addAnnotationToList([element.id, {'id': newID}, annotationLeftTimeStamp, duration], true);
    } else {
        for (let i = 0; i < emotionButtons.length; i++) {
            if (emotionButtons.item(i) !== element)
                console.log("unpressed " + emotionButtons.item(i).id);
            if (emotionButtons.item(i).getAttribute("aria-pressed") === "true") {
                emotionButtons.item(i).parentElement.style.background = "";
                emotionButtons.item(i).setAttribute("aria-pressed", "false");
            }
        }
        if (vid !== undefined) {
            emotionTimer = vid.currentTime;
        } else {
            annotationLeftTimeStamp = new Date().getTime() - recordTimer;
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

    let button_edit = "<button title='Edit Annotation' onclick='editAnnot(this)' id=\"" + "edit_" + annotation[1]['id'] + "\" class=\"edit_ann\">???</button>";
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
    btn.innerHTML = "???";
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

