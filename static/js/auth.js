document.addEventListener("DOMContentLoaded", function () {
    const authButton = document.getElementById("authButton");


    const userId = localStorage.getItem("user_id");

    if (userId) {

        authButton.innerHTML = `<a href="#" id="logoutLink">Log out</a>`;
        document.getElementById("logoutLink").addEventListener("click", logoutUser);
    } else {

        authButton.innerHTML = `<a href="/login">Log in</a>`;
    }
});


const logoutUser = async () => {
    try {
        const response = await fetch("http://127.0.0.1:3000/api/logout", {
            method: "POST",
            credentials: "include",
        });

        const data = await response.json();
        alert(data.message);
        console.log("User logged out");


        localStorage.removeItem("user_id");


        window.location.href = "/login";
    } catch (error) {
        console.error("Logout failed:", error);
        alert("Logout failed. Please try again.");
    }
};
