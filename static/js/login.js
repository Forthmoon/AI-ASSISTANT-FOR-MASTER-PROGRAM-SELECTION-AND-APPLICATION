document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("loginForm");

  if (!loginForm) {
      console.error(" Error: loginForm not found!");
      return;
  }

  console.log("loginForm found, adding event listener...");

  loginForm.addEventListener("submit", function (event) {
      event.preventDefault();
      loginUser();
  });
});

const loginUser = async () => {
  const email = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const messageBox = document.getElementById("loginMessage");


  messageBox.innerHTML = "";

  if (!email || !password) {
      alert("Please enter both email and password.");
      return;
  }

  try {
      console.log("📢 Sending login request...");

      const response = await fetch("http://127.0.0.1:3000/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
          credentials: "include",
      });

      console.log("🔍 Response status:", response.status);


      let data;
      try {
          data = await response.json();
      } catch (error) {
          console.error("Error parsing JSON response:", error);
          messageBox.innerHTML = `<p style="color: red;">Unexpected server response. Please try again later.</p>`;
          return;
      }

      console.log("🔍 Response data:", data);

      if (response.ok && data.user_id) {

          messageBox.innerHTML = `<p style="color: green;">Login successful! You can now navigate.</p>`;
          localStorage.setItem("user_id", data.user_id);


          document.querySelector(".login-form").style.display = "none";


          authButton.innerHTML = `<a href="#" onclick="logoutUser()">Log out</a>`;

      } else {

          messageBox.innerHTML = `<p style="color: red;">${data.message || "Login failed"}</p>`;
      }
  } catch (error) {
      console.error("🔥 Login request failed:", error);
      messageBox.innerHTML = `<p style="color: red;">Login request failed. Please check your network connection and try again.</p>`;
  }
};