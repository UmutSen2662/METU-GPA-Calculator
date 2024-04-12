let timeout = null;
let timeout2 = null;
document.addEventListener("change", function(event) {
    clearTimeout(timeout);
    timeout = setTimeout(function () {
        if (event.target.id[0] == "c" & event.target.value == "") {
            event.target.value = 0;
        };
        fetch("/change_course", {
            method: "POST",
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: new URLSearchParams({'id': event.target.id, 'value': event.target.value})
        }).then((res) => res.json()).then((GPAs) => {
            writeGPA(GPAs);
        });
    }, 300);
}, false);

fetch("https://raw.githubusercontent.com/UmutSen2662/METU-NCC-Course-Scraper/main/course_names.json").then((res) => res.json()).then(function (data) {
    const datalist = document.getElementById("courses");
    data.forEach(function (course_name) {
        const option = document.createElement("option");
        option.value = course_name;
        datalist.appendChild(option);
    });
});

function writeGPA(GPAs){
    let i = 0;
    const displays = document.getElementsByClassName("GPADisplay");
    Array.from(displays).forEach(function (display) {
        display.textContent = "G:" + GPAs["g"][i] + " / C:" + GPAs["c"][i];
        i += 1;
    });
    const CGPADisplay = document.getElementById("CGPADisplay");
    CGPADisplay.textContent = "CUMULATIVE GPA : " + GPAs["c"][GPAs["c"].length - 1]
};

function openTab(evt, tabName) {
    clearTimeout(timeout2);
    timeout2 = setTimeout(function () {
        fetch("/change_year/" + tabName.slice(-1));
    }, 100);

    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i+=1) {
      tabcontent[i].style.display = "none";
    }

    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i+=1) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    document.getElementById(tabName).style.display = "grid";
    evt.currentTarget.className += " active";
};

function openNav() {
    if (window.innerWidth / window.innerHeight < 2 / 3){
        document.getElementById("mySidenav").style.width = "100%";
    } else {
        document.getElementById("mySidenav").style.width = "20rem";
        document.getElementById("main").style.marginRight = "20rem";
    }
};
function closeNav() {
    document.getElementById("main").style.marginRight = "0";
    document.getElementById("mySidenav").style.width = "0";
    const form = document.getElementById("change_password");
    if (form.className == "passwordChangeForm display") {
        form.className = "passwordChangeForm";
    }
};

function openChange() {
    const form = document.getElementById("change_password");
    if (form.className == "passwordChangeForm") {
        form.className += " display";
    } else {
        form.className = "passwordChangeForm";
    }
};

function onChange() {
    const password = document.querySelector('input[name=password1]');
    const confirm = document.querySelector('input[name=password2]');
    if (confirm.value === password.value) {
        confirm.setCustomValidity('');
    } else {
        confirm.setCustomValidity('Passwords do not match');
    }
};
