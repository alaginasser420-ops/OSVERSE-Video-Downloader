const $ = (id) => document.getElementById(id);
let currentUrl = "";
let pollTimer = null;

function showError(message) {
  $("alert").textContent = message || "حدث خطأ غير متوقع.";
  $("alert").classList.remove("hidden");
}
function clearError() {
  $("alert").textContent = "";
  $("alert").classList.add("hidden");
}
function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return "";
  const m = Math.floor(seconds / 60), s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

$("inspectBtn").addEventListener("click", async () => {
  clearError();
  const url = $("videoUrl").value.trim();
  if (!url) return showError("ألصق رابط الفيديو أولاً.");
  $("inspectBtn").disabled = true;
  $("inspectBtn").textContent = "جارٍ التحليل...";
  $("videoCard").classList.add("hidden");
  $("downloadPanel").classList.add("hidden");
  try {
    const response = await fetch("/api/info", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({url})
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "تعذر تحليل الرابط.");
    currentUrl = url;
    $("videoTitle").textContent = data.title;
    $("videoDetails").textContent = [data.uploader, formatDuration(data.duration)].filter(Boolean).join(" · ");
    if (data.thumbnail) {
      $("thumbnail").src = data.thumbnail;
      $("thumbnail").classList.remove("hidden");
    } else {
      $("thumbnail").classList.add("hidden");
    }
    $("videoCard").classList.remove("hidden");
    $("downloadPanel").classList.remove("hidden");
    $("saveLink").classList.add("hidden");
    $("progressArea").classList.add("hidden");
  } catch (error) {
    showError(error.message);
  } finally {
    $("inspectBtn").disabled = false;
    $("inspectBtn").textContent = "تحليل الرابط";
  }
});

$("downloadBtn").addEventListener("click", async () => {
  clearError();
  if (!currentUrl) return showError("حلّل الرابط أولاً.");
  $("downloadBtn").disabled = true;
  $("saveLink").classList.add("hidden");
  $("progressArea").classList.remove("hidden");
  $("progressValue").textContent = "0%";
  $("progressBar").style.width = "0%";
  $("progressMessage").textContent = "جارٍ بدء التنزيل...";
  try {
    const response = await fetch("/api/download", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({url: currentUrl, quality: $("quality").value})
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "تعذر بدء التنزيل.");
    pollTask(data.task_id);
  } catch (error) {
    showError(error.message);
    $("downloadBtn").disabled = false;
  }
});

async function pollTask(taskId) {
  clearInterval(pollTimer);
  const poll = async () => {
    try {
      const response = await fetch(`/api/tasks/${taskId}`);
      const task = await response.json();
      if (!response.ok) throw new Error(task.error || "تعذر متابعة التنزيل.");
      const pct = Math.round(task.progress || 0);
      $("progressValue").textContent = `${pct}%`;
      $("progressBar").style.width = `${pct}%`;
      $("progressMessage").textContent = task.message || "جارٍ التنزيل...";
      if (task.status === "done") {
        clearInterval(pollTimer);
        $("saveLink").href = task.download_url;
        $("saveLink").classList.remove("hidden");
        $("downloadBtn").disabled = false;
      } else if (task.status === "error") {
        clearInterval(pollTimer);
        showError(task.error || "فشل التنزيل.");
        $("downloadBtn").disabled = false;
      }
    } catch (error) {
      clearInterval(pollTimer);
      showError(error.message);
      $("downloadBtn").disabled = false;
    }
  };
  await poll();
  pollTimer = setInterval(poll, 1000);
}
