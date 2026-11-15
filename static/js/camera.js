/* Laptop webcam: open, capture (canvas), retake, analyze. */
(() => {
  const $ = s => document.querySelector(s); if (!$("#video")) return;
  const video = $("#video"), canvas = $("#canvas"), prev = $("#preview");
  let stream = null, timer = null, shot = null;
  const err = m => { const e = $("#errBox"); e.textContent = m || ""; e.classList.toggle("d-none", !m); };
  const step = n => [1, 2, 3].forEach(i => $("#s" + i).classList.toggle("active", i <= n));
  function ui(state) {   // idle | live | shot
    $("#grpLive").classList.toggle("d-none", state === "shot"); $("#grpShot").classList.toggle("d-none", state !== "shot");
    $("#btnCapture").disabled = state !== "live"; $("#btnOpen").disabled = state === "live";
    $("#guide").classList.toggle("d-none", state !== "live"); $("#off").classList.toggle("d-none", state !== "idle");
    prev.classList.toggle("d-none", state !== "shot"); video.classList.toggle("d-none", state === "shot");
    $("#stCam").textContent = state === "live" ? "Ready" : state === "shot" ? "Captured" : "Off";
    if (state !== "live") { $("#stLight").textContent = "—"; $("#stQual").textContent = "—"; }
  }
  function stop() { clearInterval(timer); if (stream) stream.getTracks().forEach(t => t.stop()); stream = null; video.srcObject = null; }

  $("#btnOpen").onclick = async () => {
    err("");
    if (!navigator.mediaDevices?.getUserMedia) return err("Camera is not supported in this browser. Use Chrome or Edge on localhost.");
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
      video.srcObject = stream; await video.play(); ui("live"); step(1);
      const c = document.createElement("canvas"); c.width = 64; c.height = 48; const x = c.getContext("2d", { willReadFrequently: true });
      timer = setInterval(() => {   // simple live lighting estimate from mean luminance
        if (!video.videoWidth) return; x.drawImage(video, 0, 0, 64, 48); const d = x.getImageData(0, 0, 64, 48).data; let s = 0;
        for (let i = 0; i < d.length; i += 4) s += .299 * d[i] + .587 * d[i + 1] + .114 * d[i + 2];
        const m = s / (d.length / 4), l = m < 60 ? "Too Dark" : m > 205 ? "Too Bright" : "Good";
        $("#stLight").textContent = l; $("#stQual").textContent = l === "Good" ? "Acceptable" : "Poor";
      }, 700);
    } catch (e) {
      err({ NotAllowedError: "Camera permission denied.", PermissionDeniedError: "Camera permission denied.", NotFoundError: "No camera found.",
            NotReadableError: "Camera is already in use by another application.", SecurityError: "Open the app at http://127.0.0.1:5000" }[e.name] || "Unable to open the camera.");
      ui("idle");
    }
  };
  $("#btnCapture").onclick = () => {
    if (!stream || !video.videoWidth) return err("Please capture an image.");
    const w = Math.min(video.videoWidth, 800), h = Math.round(w * video.videoHeight / video.videoWidth);
    canvas.width = w; canvas.height = h; canvas.getContext("2d").drawImage(video, 0, 0, w, h);
    shot = canvas.toDataURL("image/jpeg", .92); prev.src = shot; stop(); ui("shot"); step(2); err("");
  };
  $("#btnRetake").onclick = () => { shot = null; err(""); ui("idle"); step(1); $("#btnOpen").click(); };
  $("#btnAnalyze").onclick = async () => {
    if (!shot) return err("Please capture an image.");
    const b = $("#btnAnalyze"); b.disabled = true; b.textContent = "Analyzing…"; step(3); err("");
    try {
      const r = await fetch("/analyze", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": document.querySelector('meta[name=csrf]').content }, body: JSON.stringify({ image: shot }) });
      const j = await r.json();
      if (!r.ok || !j.redirect) throw new Error(j.error || "Unable to analyze image.");
      location.href = j.redirect;
    } catch (e) { err(e.message || "Unable to analyze image."); b.disabled = false; b.textContent = "ANALYZE IMAGE"; step(2); }
  };
  window.addEventListener("pagehide", stop); ui("idle");
})();
