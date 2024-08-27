let timeout = null;
let timeout2 = null;
let timeout3 = null;
let csv = null;

function indexEventListeners(){
    // listen for changes to courses and update values after delay
    document.addEventListener("change", function(event) {
        if (event.target.className !== "formInput" && event.target.id !== "import") {
            clearTimeout(timeout);
            timeout = setTimeout(function () {
                if (event.target.id[0] == "c"){
                    if (event.target.value == "", event.target.validity.rangeUnderflow){
                        event.target.value = 0;
                    } else if (event.target.validity.rangeOverflow){
                        event.target.value = 10;
                    }
                }
                fetch("/change_course", {
                    method: "POST",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'id': event.target.id, 'value': event.target.value})
                }).then((res) => res.json()).then((data) => {
                    writeGPA(data);
                });
            }, 300);
        } else if (event.target.id == "import") {
            if (event.target.files[0]) {
                if (event.target.files[0].type == "text/csv") {
                    csv = event.target.files[0];
                    document.getElementById("import_btn").style.display = "block";
                    event.target.parentNode.childNodes[1].innerText = "Selected file\n" + event.target.files[0].name;
                }
            } else {
                csv = null;
                document.getElementById("import_btn").style.display = "none";
                event.target.parentNode.childNodes[1].innerText = "Select a csv file";
            }
        }
    }, false);

    // at page load fetch gpa values from server, then fetch course names from my github
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

    // listen to htmx requests and update gpa values after delay
    document.addEventListener("htmx:afterRequest", function() {
        clearTimeout(timeout3);
        timeout3 = setTimeout(function () {
            fetch("/get_gpa").then((res) => res.json()).then((data) => {
                writeGPA(data);
            });
        }, 500);
    }, false);
};

function Send_csv() {
    if (csv) {
        var reader = new FileReader();
        reader.readAsText(csv, "UTF-8");
        reader.onload = function (evt) {
            fetch("/", {
                method: "POST",
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({'csv': evt.target.result})
            }).then(() => location.href = "/");
        }
    }
}

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
    const tablinks = document.querySelectorAll(".tablinks");
    const tabcontent = document.querySelectorAll(".tabcontent");
    const activeLink = document.querySelector(".tablinks.active");

    tablinks.forEach(link => link.classList.remove("active"));
    tabcontent.forEach(content => content.style.display = "none");

    evt.currentTarget.classList.add("active");
    document.getElementById(tabName).style.display = "grid";

    if (activeLink.innerText !== evt.currentTarget.innerText) {
        clearTimeout(timeout2);
        timeout2 = setTimeout(() => {
            fetch(`/change_year/${tabName.replace("Year ", "")}`);
        }, 100);
    }
};

function openNav() {
    if (window.innerWidth < 940) {
        document.getElementById("dimmer").style.display = "block";
    } else {
        document.getElementById("main").style.marginRight = "20rem";
    }
    document.getElementById("mySidenav").style.width = "20rem";
};
function closeNav() {
    document.getElementById("dimmer").style.display = "none";
    document.getElementById("main").style.marginRight = "0";
    document.getElementById("mySidenav").style.width = "0";
    document.querySelectorAll('.display').forEach((elm) => {
        elm.classList.remove("display");
    })
};

function toggleContainer(type) {
    const toggleContainerMap = {
        "P": document.getElementById("change_password"),
        "A": document.getElementById("about_section"),
        "C": document.getElementById("contact_section"),
        "D": document.getElementById("data_section")
    };
    const container = toggleContainerMap[type];
    container.classList.toggle("display");
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
