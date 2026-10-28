const screens = document.querySelectorAll(".screen");

function showScreen(screenId) {
  screens.forEach(screen => {
    screen.classList.add("hidden");
  });

  document.getElementById(screenId).classList.remove("hidden");
}


function getUsers() {
  return JSON.parse(localStorage.getItem("demoUsers") || "{}");
}

document.getElementById("registerForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    const name = document.getElementById("registerName").value.trim();
    const email = document.getElementById("registerEmail")
      .value.trim().toLowerCase();
    const password = document.getElementById("registerPassword").value;
    const message = document.getElementById("registerMessage");

    const users = getUsers();

    if (users[email]) {
      message.textContent = "An account with this email already exists.";
      return;
    }

    
    users[email] = { name, password };

    localStorage.setItem("demoUsers", JSON.stringify(users));

    message.textContent = "Account created! You can now log in.";
    document.getElementById("registerForm").reset();

    setTimeout(() => showScreen("login"), 1000);
  });


document.getElementById("loginForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail")
      .value.trim().toLowerCase();
    const password = document.getElementById("loginPassword").value;
    const message = document.getElementById("loginMessage");

    const users = getUsers();
    const user = users[email];

    if (!user || user.password !== password) {
      message.textContent = "Invalid email or password.";
      return;
    }

    // Demo navigation only; not a secure session.
    document.getElementById("welcomeMessage").textContent =
      `Welcome, ${user.name}!`;

    document.getElementById("loginForm").reset();
    message.textContent = "";

    showScreen("dashboard");
  });


function logout() {
  showScreen("home");
}