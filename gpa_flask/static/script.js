let timeout = null;
let timeout2 = null;
let timeout3 = null;

function indexEventListeners(){
    document.addEventListener("change", function(event) {
        if (event.target.className !== "formInput"){
            clearTimeout(timeout);
            timeout = setTimeout(function () {
                if (event.target.id[0] == "c" & event.target.value == "") {
                    event.target.value = 0;
                };
                fetch("/change_course", {
                    method: "POST",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'id': event.target.id, 'value': event.target.value})
                }).then((res) => res.json()).then((data) => {
                    writeGPA(data);
                });
            }, 300);
        }
    }, false);

    document.addEventListener("DOMContentLoaded", function() {
        fetch("/get_gpa").then((res) => res.json()).then((data) => {
            writeGPA(data);
        });
        fetch("https://raw.githubusercontent.com/UmutSen2662/METU-NCC-Course-Scraper/main/course_names.json").then((res) => res.json()).then(function (data) {
            const datalist = document.getElementById("courses");
            data.forEach(function (course_name) {
                const option = document.createElement("option");
                option.value = course_name;
                datalist.appendChild(option);
            });
        });
    }, false);

    document.addEventListener("htmx:afterRequest", function() {
        clearTimeout(timeout3);
        timeout3 = setTimeout(function () {
            fetch("/get_gpa").then((res) => res.json()).then((data) => {
                writeGPA(data);
            });
        }, 500);
    }, false);
};

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
    currentYear = document.getElementsByClassName("tablinks active")[0].innerText.slice(-1);
    newYear = tabName.slice(-1);
    if (currentYear == newYear)
        return;

    clearTimeout(timeout2);
    timeout2 = setTimeout(function () {
        fetch("/change_year/" + newYear);
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
    document.querySelectorAll('.display').forEach((elm) => {
        elm.classList.remove("display");
    })
};

function toggleContainer(type) {
    let container = null
    switch (type) {
        case "P":
            container = document.getElementById("change_password");
            break;
        case "A":
            container = document.getElementById("about_section");
            break;
        case "C":
            container = document.getElementById("contact_section");
            break;
    }
    if (container.classList.contains("display")){
        container.classList.remove("display");
    } else {
        container.classList.add("display");    
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
