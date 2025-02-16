document.addEventListener("DOMContentLoaded", function () {
  const chatInterface = document.getElementById("chatInterface");
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const resultsContainer = document.getElementById("results");


  sendButton.addEventListener("click", function () {
    const message = userInput.value.trim();
    if (!message) return;
    appendUserMessage(message);
    userInput.value = "";


    const waitingBubble = appendWaitingMessage();


    sendMessageToBackend(message)
      .then((data) => {
        removeWaitingMessage(waitingBubble);
        appendAssistantMessage(data.response || "No response from assistant.");


        if (data.results && data.results.length > 0) {
          displayResults(data.results);
        } else if (data.programs && data.programs.length > 0) {
          displayRecommendedPrograms(data.programs);
        }
      })
      .catch((error) => {
        removeWaitingMessage(waitingBubble);
        appendAssistantMessage("Error: " + error);
      });
  });


  function appendUserMessage(message) {
    const div = document.createElement("div");
    div.className = "chat-message user";
    div.innerHTML = `<div class="bubble">${message}</div>`;
    chatInterface.appendChild(div);
    chatInterface.scrollTop = chatInterface.scrollHeight;
  }


  function appendAssistantMessage(message) {

    message = convertMarkdownBold(message);
    const div = document.createElement("div");
    div.className = "chat-message assistant";
    div.innerHTML = `<img class="assistant-avatar" src="/static/User_Interface/OIG4.jpeg" alt="Assistant Avatar">
                     <div class="bubble">${message}</div>`;
    chatInterface.appendChild(div);
    chatInterface.scrollTop = chatInterface.scrollHeight;
  }


  function appendWaitingMessage() {
    const div = document.createElement("div");
    div.className = "chat-message assistant waiting";
    div.innerHTML = `<img class="assistant-avatar" src="/static/User_Interface/OIG4.jpeg" alt="Assistant Avatar">
                     <div class="bubble waiting-message">Generating recommendations, please wait...</div>`;
    chatInterface.appendChild(div);
    chatInterface.scrollTop = chatInterface.scrollHeight;
    return div;
  }


  function removeWaitingMessage(div) {
    if (div && div.parentNode) {
      div.parentNode.removeChild(div);
    }
  }


async function sendMessageToBackend(message) {
  try {
    const response = await fetch("http://127.0.0.1:3000/api/recommendation-chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();

    // 优先使用 data.programs 更新推荐列表
    if (data.programs && data.programs.length > 0) {
      displayRecommendedPrograms(data.programs);
    }
    return data;
  } catch (err) {
    console.error("Error sending message:", err);
    throw err;
  }
}



  function convertMarkdownBold(text) {
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  }


  function displayRecommendedPrograms(programs) {
    resultsContainer.innerHTML = "";
    if (!programs || programs.length === 0) {
      resultsContainer.innerHTML = "<p>No recommended programs found. Please try again with different criteria.</p>";
      return;
    }
    programs.forEach((program) => {
      const programElement = document.createElement("div");
      programElement.classList.add("result-item");
      programElement.innerHTML = `
          <h3>${program.university_name}</h3>
          <p>Program: ${program.program_name}</p>
          <button class="save-button" onclick="saveProgram(${program.program_id}, '${program.program_name}', '${program.university_name}')">Save to Overview</button>
      `;
      resultsContainer.appendChild(programElement);
    });
  }


  function displayResults(results) {
    resultsContainer.innerHTML = "";
    if (!results || results.length === 0) {
      resultsContainer.innerHTML = "<p>No recommendations found. Please try again with different criteria.</p>";
      return;
    }
    results.forEach((item) => {

      const programId = item.program_id;
      const programName = item.program_name;
      const universityName = item.university_name;
      const explanation = convertMarkdownBold(item.explanation || "N/A");

      const resultDiv = document.createElement("div");
      resultDiv.className = "result-item";
      resultDiv.innerHTML = `
        <h3>${universityName}</h3>
        <p>Program: ${programName}</p>
        <p class="explanation">Recommendation: ${explanation}</p>
        <button class="save-button" onclick="saveProgram(${programId}, '${programName}', '${universityName}')">Save to Overview</button>
      `;
      resultsContainer.appendChild(resultDiv);
    });
  }


  window.saveProgram = async function (programId, programName, universityName) {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      alert("Please log in first.");
      return;
    }
    try {
      const response = await fetch("http://127.0.0.1:3000/api/save-program", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          program_id: programId,
          program_name: programName,
          university_name: universityName
        }),
      });
      const data = await response.json();
      alert(data.message);
    } catch (error) {
      console.error("Error saving program:", error);
      alert("Failed to save program.");
    }
  };
});
