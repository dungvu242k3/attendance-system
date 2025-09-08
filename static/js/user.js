const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const attendanceBtn = document.getElementById('attendance-btn');
const employeeName = document.getElementById('employee-name');
const statusEl = document.getElementById('status');
const currentTime = document.getElementById('currentTime');
const currentDate = document.getElementById('currentDate');

function updateClock() {
  const now = new Date();
  currentTime.textContent = now.toLocaleTimeString('vi-VN', { hour12: false });
  currentDate.textContent = now.toLocaleDateString('vi-VN', { weekday:'long', year:'numeric', month:'long', day:'numeric' });
}
setInterval(updateClock, 1000);
updateClock();

navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
  })
  .catch(err => {
    console.error("Không thể mở camera:", err);
    statusEl.textContent = "Lỗi camera: " + err.message;
  });

function captureImage() {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0);
  return canvas.toDataURL('image/jpeg');
}

async function recognizeFace(imageData) {
  const resp = await fetch('/api/recognize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: imageData })
  });
  return await resp.json();
}

async function markAttendance(employeeCode, imageData) {
  const resp = await fetch('/api/recognize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_code: employeeCode, image: imageData })
  });
  return await resp.json();
}

attendanceBtn.addEventListener('click', async () => {
  statusEl.textContent = "Đang xử lý...";

  const imgData = captureImage();
  const recogResult = await recognizeFace(imgData);

  if (recogResult.status !== "ok") {
    employeeName.textContent = recogResult.name || "Không xác định";
    statusEl.textContent = recogResult.message || "Không nhận diện được";
    return;
  }

  const attResult = await markAttendance(recogResult.employee_code, imgData);

  employeeName.textContent = recogResult.name;
  statusEl.textContent = attResult.message;
});
