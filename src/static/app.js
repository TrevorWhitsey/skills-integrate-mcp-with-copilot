document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const loginForm = document.getElementById("login-form");
  const loginEmail = document.getElementById("login-email");
  const loginPassword = document.getElementById("login-password");
  const accountInfo = document.getElementById("account-info");
  const accountStatus = document.getElementById("account-status");
  const accountEnrollments = document.getElementById("account-enrollments");
  const authMessage = document.getElementById("auth-message");
  const logoutButton = document.getElementById("logout-button");
  const signupContainer = document.getElementById("signup-container");
  const staffRoles = ["teacher", "coordinator"];
  let currentUser = null;

  function isStaff() {
    return currentUser && staffRoles.includes(currentUser.role);
  }

  function renderAuthState() {
    loginForm.classList.toggle("hidden", Boolean(currentUser));
    accountInfo.classList.toggle("hidden", !currentUser);
    signupContainer.classList.toggle("hidden", !isStaff());
    accountStatus.textContent = currentUser
      ? `Signed in as ${currentUser.name || currentUser.email} (${currentUser.role})`
      : "Sign in with your school account to manage enrollment.";
    const enrollments = currentUser?.enrollments || [];
    accountEnrollments.textContent = currentUser
      ? `Your enrollments: ${enrollments.length ? enrollments.join(", ") : "None"}`
      : "";
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) => `<li><span class="participant-email">${email}</span>${
                      isStaff()
                        ? `<button class="delete-btn" data-activity="${name}" data-email="${email}" aria-label="Unregister ${email}">Remove</button>`
                        : ""
                    }</li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      activitiesList.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("student-email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail.value, password: loginPassword.value }),
      });
      const result = await response.json();

      if (!response.ok) {
        authMessage.textContent = result.detail || "Unable to sign in.";
        authMessage.className = "error";
        authMessage.classList.remove("hidden");
        return;
      }

      currentUser = result.user;
      loginForm.reset();
      authMessage.classList.add("hidden");
      renderAuthState();
      await fetchActivities();
    } catch (error) {
      authMessage.textContent = "Failed to sign in. Please try again.";
      authMessage.className = "error";
      authMessage.classList.remove("hidden");
      console.error("Error signing in:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      if (!response.ok) {
        throw new Error("The server could not end the session.");
      }
      currentUser = null;
      renderAuthState();
      await fetchActivities();
    } catch (error) {
      authMessage.textContent = "Failed to sign out. Please try again.";
      authMessage.className = "error";
      authMessage.classList.remove("hidden");
      console.error("Error signing out:", error);
    }
  });

  async function initialize() {
    try {
      const response = await fetch("/auth/me");
      if (response.ok) {
        const result = await response.json();
        currentUser = result.user;
      }
    } catch (error) {
      console.error("Error checking school account:", error);
    }
    renderAuthState();
    await fetchActivities();
  }

  initialize();
});
