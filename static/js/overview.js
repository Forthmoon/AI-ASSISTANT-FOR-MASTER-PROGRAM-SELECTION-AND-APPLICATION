document.addEventListener("DOMContentLoaded", async function () {
    const savedProgramsContainer = document.getElementById("saved-programs");
    const generateSummaryButton = document.getElementById("generateSummary");

    try {
        const userId = localStorage.getItem("user_id");

        if (!userId) {
            alert("Please log in to view saved programs.");
            savedProgramsContainer.innerHTML = "<p>Please log in first.</p>";
            return;
        }


        const response = await fetch(`http://127.0.0.1:3000/api/get-saved-programs?user_id=${userId}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            }
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();
        console.log("API Response:", data);

        if (data.programs && data.programs.length > 0) {
            savedProgramsContainer.innerHTML = "";
            data.programs.forEach(program => {
                const programDiv = document.createElement("div");
                programDiv.className = "program-card";

                programDiv.innerHTML = `
                    <div class="program-details">
                        <div class="program-title">${program.program_name}</div>
                        <div class="university">${program.university_name}</div>
                    </div>
                `;
                savedProgramsContainer.appendChild(programDiv);
            });
        } else {
            savedProgramsContainer.innerHTML = "<p>No saved programs found.</p>";
        }
    } catch (error) {
        console.error("Error loading saved programs:", error);
        savedProgramsContainer.innerHTML = "<p>Error loading saved programs. Please try again later.</p>";
    }


    generateSummaryButton.addEventListener("click", async function () {
        console.log("Generating Summary PDF...");

        try {

            const userId = localStorage.getItem("user_id");
            if (!userId) {
                alert("Please log in to generate the summary PDF.");
                return;
            }


            const response = await fetch(`http://127.0.0.1:3000/api/generate-summary-pdf?user_id=${userId}`);

            if (!response.ok) {
                throw new Error("Failed to generate summary PDF.");
            }


            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `user_${userId}_summary.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            alert("Summary PDF generated successfully!");
        } catch (error) {
            console.error("Error generating summary PDF:", error);
            alert("An error occurred while generating the summary PDF. Please try again.");
        }
    });
});

