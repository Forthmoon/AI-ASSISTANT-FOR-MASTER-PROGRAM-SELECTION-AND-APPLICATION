document.addEventListener("DOMContentLoaded", function () {
  const chatInterface = document.getElementById("chatInterface");
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const fileInput = document.getElementById("fileInput");


  sendButton.addEventListener("click", function () {
      const message = userInput.value.trim();
      if (message) {
          appendUserMessage(message);
          userInput.value = "";

          if (message.toLowerCase().includes("sql")) {
              callSqlApi(message);
          } else {
              sendMessageToBackend(message);
          }
      }
  });


  fileInput.addEventListener("change", function () {
      const file = fileInput.files[0];
      if (file && file.type === "application/pdf") {
          appendUserMessage(`📄 Uploaded: ${file.name}`);
          uploadPDFToBackend(file);
      } else {
          alert("Please upload a valid PDF file.");
      }
  });


  function appendUserMessage(message) {
      const userMessage = document.createElement("div");
      userMessage.className = "chat-message user";
      userMessage.innerHTML = `<div class="bubble">${message}</div>`;
      chatInterface.appendChild(userMessage);
      chatInterface.scrollTop = chatInterface.scrollHeight;
  }


  async function sendMessageToBackend(message) {
      try {
          const response = await fetch("http://127.0.0.1:3000/api/application/chat", {
              method: "POST",
              headers: {
                  "Content-Type": "application/json",
              },
              body: JSON.stringify({ message }),
          });
          const data = await response.json();
          console.log("Received AI Response:", data);
          appendAssistantMessage(data.response || "No response from assistant.");
      } catch (error) {
          console.error("Error sending message:", error);
          appendAssistantMessage("Error communicating with assistant.");
      }
  }


  async function callSqlApi(msg) {
      try {

          const userId = localStorage.getItem("user_id");
          if (!userId) {
              alert("Please log in first.");
              return;
          }
          const response = await fetch("http://127.0.0.1:3000/api/application/chat-sql", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ user_id: parseInt(userId), message: msg }),
          });
          const data = await response.json();
          console.log("✅ Received GPT-SQL Response:", data);
          appendAssistantMessage(data.answer || "No SQL response from assistant.");
      } catch (err) {
          console.error("Error calling /chat-sql:", err);
          appendAssistantMessage("Error calling GPT-SQL API");
      }
  }


  async function uploadPDFToBackend(file) {
      const formData = new FormData();
      formData.append("pdf_file", file);

      try {
          const response = await fetch("http://127.0.0.1:3000/api/application/upload_pdf", {
              method: "POST",
              body: formData,
          });
          const data = await response.json();
          appendAssistantMessage(data.message || "PDF uploaded successfully.");
      } catch (error) {
          console.error("Error uploading PDF:", error);
          appendAssistantMessage("Error uploading PDF.");
      }
  }


  function appendAssistantMessage(message) {
      const assistantMessage = document.createElement("div");
      assistantMessage.className = "chat-message assistant";
      assistantMessage.innerHTML = `
          <img class="assistant-avatar" src="/static/User_Interface/OIG4.jpeg" alt="Assistant Logo">
          <div class="bubble">${message}</div>`;
      chatInterface.appendChild(assistantMessage);
      chatInterface.scrollTop = chatInterface.scrollHeight;
  }
});

