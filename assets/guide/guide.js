(() => {
  "use strict";

  const roleInputs = [...document.querySelectorAll('input[name="guide-role"]')];
  const progressChecks = [...document.querySelectorAll("[data-progress]")];
  const progressLabel = document.querySelector("[data-progress-label]");
  const progressBar = document.querySelector("[data-progress-bar]");
  const printButton = document.querySelector("[data-print]");
  const openCoachLinks = [...document.querySelectorAll("[data-open-coach]")];
  const copyButtons = [...document.querySelectorAll("[data-copy-target]")];
  const copyStatus = document.querySelector("[data-copy-status]");

  function syncRole() {
    const selectedRole = roleInputs.find((input) => input.checked)?.value;
    if (selectedRole) document.body.dataset.role = selectedRole;
  }

  function updateProgress() {
    const completed = progressChecks.filter((checkbox) => checkbox.checked).length;
    const total = progressChecks.length;
    if (progressLabel) progressLabel.textContent = `${completed}/${total}`;
    if (progressBar) progressBar.style.width = `${total ? (completed / total) * 100 : 0}%`;
  }

  function revealCoachTarget() {
    const coachHashes = new Set(["#coach", "#coach-start"]);
    if (!coachHashes.has(window.location.hash)) return false;
    const coachInput = roleInputs.find((input) => input.value === "coach");
    if (coachInput) coachInput.checked = true;
    syncRole();
    window.requestAnimationFrame(() => {
      document.querySelector(window.location.hash)?.scrollIntoView();
    });
    return true;
  }

  async function copyCommand(button) {
    const target = document.getElementById(button.dataset.copyTarget);
    if (!target) return;
    const command = target.innerText.trim();
    try {
      await navigator.clipboard.writeText(command);
    } catch {
      const fallback = document.createElement("textarea");
      fallback.value = command;
      fallback.setAttribute("readonly", "");
      fallback.style.position = "fixed";
      fallback.style.opacity = "0";
      document.body.append(fallback);
      fallback.select();
      document.execCommand("copy");
      fallback.remove();
    }
    if (copyStatus) copyStatus.textContent = "Đã sao chép lệnh. Dán vào Terminal hoặc Colab cell.";
    button.textContent = "Đã sao chép";
    window.setTimeout(() => { button.textContent = "Sao chép"; }, 1600);
  }

  roleInputs.forEach((input) => input.addEventListener("change", syncRole));
  openCoachLinks.forEach((link) => link.addEventListener("click", () => {
    const coachInput = roleInputs.find((input) => input.value === "coach");
    if (coachInput) coachInput.checked = true;
    syncRole();
  }));
  copyButtons.forEach((button) => button.addEventListener("click", () => copyCommand(button)));
  progressChecks.forEach((checkbox) => checkbox.addEventListener("change", updateProgress));
  if (printButton) printButton.addEventListener("click", () => window.print());
  window.addEventListener("hashchange", revealCoachTarget);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.querySelector(".lightbox:target")) {
      const returnHash = document.querySelector(".lightbox:target .lightbox-toolbar a")?.hash || "#top";
      window.location.hash = returnHash;
      document.querySelector(returnHash)?.focus({ preventScroll: true });
    }
  });

  if (!revealCoachTarget()) syncRole();
  updateProgress();
})();
