/* Trend line graph (Chart.js) fed by /api/trend (authenticated, from SQL) */
(async () => {
  const c = document.getElementById("trendChart"); if (!c) return;
  const note = document.getElementById("trendNote"), box = document.getElementById("cmpBox");
  try {
    const d = await (await fetch("/api/trend")).json();
    if (!d.points) return;
    if (!d.points.length) { if (note) note.textContent = "No screenings yet. Start a screening to see your trend."; return; }
    new Chart(c, { type: "line", data: { labels: d.points.map(p => p.date), datasets: [{ label: "Anemia screening risk (%)",
        data: d.points.map(p => p.risk), borderColor: "#590907", backgroundColor: "rgba(232,210,181,.5)", fill: true, tension: .35,
        pointBackgroundColor: "#590907", pointRadius: 5, borderWidth: 3 }] },
      options: { plugins: { legend: { display: false } }, scales: {
        y: { min: 0, max: 100, title: { display: true, text: "Screening risk (%)" }, grid: { color: "rgba(165,167,155,.3)" } },
        x: { title: { display: true, text: "Screening date" }, grid: { display: false } } } } });
    if (c.dataset.quiet) return;
    if (d.comparison) {
      const x = d.comparison, sg = x.change > 0 ? "+" : "";
      box.innerHTML = `<div class="col-4 stat"><div class="l">Previous</div><div class="v">${x.previous}%</div></div><div class="col-4 stat"><div class="l">Current</div><div class="v">${x.current}%</div></div><div class="col-4 stat"><div class="l">Change</div><div class="v">${sg}${x.change}%</div></div>`;
      note.textContent = x.message;
    } else note.textContent = "This is your first recorded screening. Future screenings will appear here for comparison.";
  } catch (e) { if (note) note.textContent = "Unable to load trend."; }
})();
