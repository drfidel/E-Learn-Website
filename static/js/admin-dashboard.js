(() => {
  function parseSeries(scriptId) {
    const node = document.getElementById(scriptId);
    if (!node) {
      return [];
    }
    try {
      return JSON.parse(node.textContent);
    } catch (error) {
      return [];
    }
  }

  function buildPath(points) {
    return points
      .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
      .join(" ");
  }

  function renderLineChart(targetId, data) {
    const target = document.getElementById(targetId);
    if (!target) {
      return;
    }

    if (!Array.isArray(data) || data.length === 0) {
      target.innerHTML = '<p class="chart-empty">No activity data available yet.</p>';
      return;
    }

    const width = 680;
    const height = 210;
    const padding = { top: 18, right: 8, bottom: 22, left: 14 };
    const values = data.map((item) => Number(item.value) || 0);
    const max = Math.max(...values, 1);

    const points = values.map((value, index) => {
      const x =
        padding.left +
        (index * (width - padding.left - padding.right)) / Math.max(values.length - 1, 1);
      const y =
        height - padding.bottom - (value / max) * (height - padding.top - padding.bottom);
      return { x: Number(x.toFixed(2)), y: Number(y.toFixed(2)) };
    });

    const yGrid = [0.25, 0.5, 0.75].map((fraction) => {
      return (height - padding.bottom) - (height - padding.top - padding.bottom) * fraction;
    });

    const pointMarkup = points
      .map((point) => `<circle class="chart-point" cx="${point.x}" cy="${point.y}" r="3"></circle>`)
      .join("");

    const gridMarkup = yGrid
      .map((lineY) => `<line class="chart-grid-line" x1="${padding.left}" y1="${lineY}" x2="${width - padding.right}" y2="${lineY}"></line>`)
      .join("");

    const firstLabel = data[0]?.label || "";
    const lastLabel = data[data.length - 1]?.label || "";
    const maxLabel = max.toFixed(max % 1 === 0 ? 0 : 2);

    target.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Chart">
        ${gridMarkup}
        <path class="chart-line" d="${buildPath(points)}"></path>
        ${pointMarkup}
      </svg>
      <div class="chart-caption">
        <span>${firstLabel}</span>
        <span>Peak: ${maxLabel}</span>
        <span>${lastLabel}</span>
      </div>
    `;
  }

  renderLineChart("enrollment-chart", parseSeries("admin-enrollment-series"));
  renderLineChart("revenue-chart", parseSeries("admin-revenue-series"));
})();
