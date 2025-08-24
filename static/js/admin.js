
async function deleteEmployee(id) {
  if (!confirm("Bạn có chắc chắn muốn xoá nhân viên này?")) return;

  try {
    const res = await fetch(`/admin/delete_employee/${id}`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json"
      }
    });

    const data = await res.json();

    showToast(data.message || "Xong", data.status === "ok" ? "success" : "error");

    if (data.status === "ok") {
      setTimeout(() => location.reload(), 1000);
    }

  } catch (err) {
    console.error(err);
    showToast("Có lỗi xảy ra khi xoá nhân viên!", "error");
  }
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `fixed bottom-5 right-5 px-4 py-2 rounded-lg shadow-lg text-white z-50
    ${type === "success" ? "bg-green-600" : type === "error" ? "bg-red-600" : "bg-gray-700"}`;
  toast.innerText = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
  }, 2500);

  setTimeout(() => toast.remove(), 3000);
}

async function deleteEmployee(id) {
  if (!confirm("Bạn có chắc chắn muốn xoá nhân viên này?")) return;

  try {
    const res = await fetch(`/admin/delete_employee/${id}`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json"
      }
    });

    const data = await res.json();

    showToast(data.message || "Xong", data.status === "ok" ? "success" : "error");

    if (data.status === "ok") {
      setTimeout(() => location.reload(), 1000);
    }

  } catch (err) {
    console.error(err);
    showToast("Có lỗi xảy ra khi xoá nhân viên!", "error");
  }
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `fixed bottom-5 right-5 px-4 py-2 rounded-lg shadow-lg text-white z-50
    ${type === "success" ? "bg-green-600" : type === "error" ? "bg-red-600" : "bg-gray-700"}`;
  toast.innerText = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
  }, 2500);

  setTimeout(() => toast.remove(), 3000);
}
