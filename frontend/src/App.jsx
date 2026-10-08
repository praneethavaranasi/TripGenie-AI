import React, { useRef, useState } from "react";
import backdropImage from "./assets/public/TripGenie Backdrop image.png";

const API_URL = "http://127.0.0.1:8000";

const exampleRequest =
  "Plan a 5-day trip to Goa for 3 people under ₹50,000 with beaches, nightlife and local food";

function formatCurrency(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return String(value);
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(number);
}

function formatItineraryActivity(item) {
  if (typeof item === "string") {
    return item;
  }

  if (item && typeof item === "object") {
    return item.name || item.title || JSON.stringify(item);
  }

  return String(item ?? "");
}

function getAgentIcon(agent) {
  const icons = {
    "Supervisor Agent": "🧭",
    "Planner Agent": "🧠",
    "Research Agent": "🔎",
    "Budget Agent": "💰",
    "Itinerary Agent": "🗓️",
    Validation: "✓",
  };

  return icons[agent] || "🤖";
}

function statusClass(status) {
  if (status === "completed") return "completed";
  if (status === "running") return "running";
  if (status === "failed") return "failed";
  return "pending";
}

function App() {
  const [request, setRequest] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [agentTimes, setAgentTimes] = useState({});
  const [agentMessages, setAgentMessages] = useState({});
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [error, setError] = useState("");
  const eventSourceRef = useRef(null);
  const agentStartTimes = useRef({});

  const planningAgents = [
    {
      name: "Supervisor Agent",
      description: "Understanding your travel requirements",
    },
    {
      name: "Planner Agent",
      description: "Creating your personalized travel strategy",
    },
    {
      name: "Research Agent",
      description: "Researching destinations, activities and food",
    },
    {
      name: "Budget Agent",
      description: "Analyzing your travel budget",
    },
    {
      name: "Itinerary Agent",
      description: "Building your day-by-day itinerary",
    },
    {
      name: "Validation",
      description: "Checking your final travel plan",
    },
  ];

  const getAgentStatus = (agentName) => agentStatuses[agentName] || "waiting";

  React.useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const startPlanning = async () => {
    const trimmedRequest = request.trim();

    if (!trimmedRequest) {
      setError("Please describe your trip before starting.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setAgentStatuses({});
    setAgentMessages({});
    setAgentTimes({});
    agentStartTimes.current = {};
    setActiveAgent(null);

    try {
      const requestId = crypto.randomUUID();
      const eventSource = new EventSource(
        `${API_URL}/plan-trip/events/${requestId}`
      );

      eventSourceRef.current = eventSource;
      let streamReady = false;
      let resolveStreamReady;
      let rejectStreamReady;
      const streamReadyPromise = new Promise((resolve, reject) => {
        resolveStreamReady = resolve;
        rejectStreamReady = reject;
      });

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "ready") {
            streamReady = true;
            resolveStreamReady();
            return;
          }

          if (data.type === "agent_started") {
            agentStartTimes.current[data.agent] = Date.now();
            setActiveAgent(data.agent);
            setAgentStatuses((previous) => ({
              ...previous,
              [data.agent]: "active",
            }));
            setAgentMessages((previous) => ({
              ...previous,
              [data.agent]: data.message,
            }));
          }

          if (data.type === "agent_completed") {
            const startedAt = agentStartTimes.current[data.agent];
            const elapsed = startedAt
              ? ((Date.now() - startedAt) / 1000).toFixed(1)
              : null;

            setAgentTimes((previous) => ({
              ...previous,
              [data.agent]: elapsed,
            }));
            setAgentStatuses((previous) => ({
              ...previous,
              [data.agent]: "completed",
            }));
            setAgentMessages((previous) => ({
              ...previous,
              [data.agent]: data.message,
            }));
            setActiveAgent((current) =>
              current === data.agent ? null : current
            );
          }

          if (data.type === "complete") {
            setAgentStatuses((previous) => ({
              ...previous,
              [data.agent]: "completed",
            }));
            setActiveAgent(null);
            eventSource.close();
            eventSourceRef.current = null;
          }
        } catch (eventError) {
          console.error("SSE event error:", eventError);
        }
      };

      eventSource.onerror = (eventError) => {
        console.error("SSE connection error:", eventError);

        if (!streamReady) {
          rejectStreamReady(
            new Error("Unable to connect to the agent progress stream.")
          );
        }
      };

      await streamReadyPromise;

      const response = await fetch(`${API_URL}/plan-trip`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          request: trimmedRequest,
          request_id: requestId,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(
          data.error || "TripGenie could not create your travel plan."
        );
      }

      setResult(data);
    } catch (err) {
      console.error(err);
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
      setActiveAgent(null);

      setError(
        err.message ||
          "Unable to connect to TripGenie AI. Make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const planAnotherTrip = () => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setResult(null);
    setError("");
    setRequest("");
    setAgentStatuses({});
    setAgentMessages({});
    setAgentTimes({});
    agentStartTimes.current = {};
    setActiveAgent(null);
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const useExample = () => {
    setRequest(exampleRequest);
    setError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const trip = result?.trip || {};
  const research = result?.research || {};
  const budget = result?.budget || {};
  const itinerary = result?.itinerary || {};
  const validation = result?.validation || {};
  const agents = result?.agent_activity || [];

  const days = Array.isArray(itinerary.days) ? itinerary.days : [];

  const downloadTripPlan = () => {
    if (!result) return;

    const escapeHtml = (value) =>
      String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    const listHtml = (items = []) =>
      Array.isArray(items)
        ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
        : "";

    const places = Array.isArray(research.recommended_places)
      ? research.recommended_places
      : [];
    const breakdown = budget.breakdown || {};
    const notes = Array.isArray(validation.notes)
      ? validation.notes
      : Array.isArray(validation.issues)
        ? validation.issues
        : [];

    const daysHtml = days
      .map(
        (day) => `
          <section class="day">
            <div class="day-title">
              <span>DAY ${escapeHtml(day.day)}</span>
              <h2>${escapeHtml(day.title || `Day ${day.day}`)}</h2>
            </div>
            <div class="schedule-grid">
              <div><h3>Morning</h3><ul>${listHtml(day.morning)}</ul></div>
              <div><h3>Afternoon</h3><ul>${listHtml(day.afternoon)}</ul></div>
              <div><h3>Evening</h3><ul>${listHtml(day.evening)}</ul></div>
            </div>
            ${
              Array.isArray(day.meals) && day.meals.length
                ? `<h3>Meals</h3><ul>${listHtml(day.meals)}</ul>`
                : ""
            }
            <div class="cost">Estimated Daily Cost: ${escapeHtml(
              formatCurrency(day.estimated_daily_cost)
            )}</div>
            ${
              day.notes
                ? `<p class="notes"><strong>Notes:</strong> ${escapeHtml(
                    day.notes
                  )}</p>`
                : ""
            }
          </section>
        `
      )
      .join("");

    const placesHtml = places
      .map(
        (place) => `
          <li>
            <strong>${escapeHtml(place.name)}</strong>
            ${place.category ? ` - ${escapeHtml(place.category)}` : ""}
            ${
              place.description
                ? `<br>${escapeHtml(place.description)}`
                : ""
            }
          </li>
        `
      )
      .join("");

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TripGenie AI - ${escapeHtml(trip.destination || "Travel Plan")}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Geist", "Geist Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f8f6; color: #17352a; line-height: 1.6; }
    .container { width: min(90%, 950px); margin: 40px auto; }
    .header { padding: 38px; margin-bottom: 20px; border-radius: 22px; background: linear-gradient(135deg, #173d2d, #285740); color: #fff; }
    .brand { font-size: 13px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #c6dbcf; }
    .header h1 { margin: 10px 0 4px; font-size: 36px; }
    .header p { margin: 0; color: #dce9e1; }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
    .card, .section { padding: 20px; border: 1px solid #e0eae4; border-radius: 16px; background: #fff; }
    .label { color: #71857c; font-size: 10px; font-weight: 700; letter-spacing: .7px; text-transform: uppercase; }
    .value { margin-top: 5px; color: #234d3a; font-size: 17px; font-weight: 700; }
    .section { margin-bottom: 18px; padding: 26px; }
    .section > h2 { margin: 0 0 14px; color: #183b2c; }
    .day { margin: 16px 0; padding: 20px; border: 1px solid #e0eae4; border-radius: 15px; background: #fcfefd; page-break-inside: avoid; }
    .day-title span { color: #4d7b60; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
    .day-title h2 { margin: 4px 0 14px; color: #254d3b; }
    .day h3 { margin: 12px 0 4px; color: #547565; font-size: 14px; }
    ul { padding-left: 20px; }
    li { margin-bottom: 5px; }
    .schedule-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .schedule-grid > div { padding: 12px; border: 1px solid #e6ede9; border-radius: 10px; }
    .schedule-grid ul { margin-bottom: 0; }
    .cost { margin-top: 16px; padding: 11px 14px; border-radius: 10px; background: #edf5ef; color: #2c5844; font-weight: 700; }
    .notes { padding: 12px 14px; border-radius: 10px; background: #f5f9f6; }
    .budget-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .budget-item { padding: 13px; border-radius: 10px; background: #f5f9f6; }
    .status { display: inline-block; padding: 6px 12px; border-radius: 20px; background: #eaf6ee; color: #3e8259; font-size: 12px; font-weight: 700; }
    .footer { padding: 22px; color: #71857c; font-size: 12px; text-align: center; }
    @media print { body { background: #fff; } .container { width: 100%; margin: 0; } .header, .section, .card { box-shadow: none; } }
    @media (max-width: 700px) { .grid { grid-template-columns: repeat(2, 1fr); } .budget-grid, .schedule-grid { grid-template-columns: 1fr; } .header { padding: 26px; } }
  </style>
</head>
<body>
  <main class="container">
    <header class="header">
      <div class="brand">TripGenie AI</div>
      <h1>${escapeHtml(trip.destination || "Your Trip")}</h1>
      <p>AI-powered personalized travel plan</p>
    </header>
    <div class="grid">
      <div class="card"><div class="label">Destination</div><div class="value">${escapeHtml(trip.destination || "—")}</div></div>
      <div class="card"><div class="label">Duration</div><div class="value">${escapeHtml(trip.duration || "—")}</div></div>
      <div class="card"><div class="label">Travelers</div><div class="value">${escapeHtml(trip.travelers ?? "—")}</div></div>
      <div class="card"><div class="label">Budget</div><div class="value">${escapeHtml(formatCurrency(trip.budget))}</div></div>
    </div>
    <section class="section">
      <h2>Trip Overview</h2>
      <p>${escapeHtml(research.destination_overview || "No destination overview was provided.")}</p>
    </section>
    <section class="section">
      <h2>Recommended Places</h2>
      ${placesHtml ? `<ul>${placesHtml}</ul>` : "<p>No recommended places were provided.</p>"}
    </section>
    <section class="section">
      <h2>Budget Analysis</h2>
      <p><span class="status">${escapeHtml(budget.status || "ANALYZED")}</span></p>
      <div class="budget-grid">
        <div class="budget-item"><strong>Accommodation</strong><br>${escapeHtml(formatCurrency(breakdown.accommodation))}</div>
        <div class="budget-item"><strong>Transportation</strong><br>${escapeHtml(formatCurrency(breakdown.transportation))}</div>
        <div class="budget-item"><strong>Food</strong><br>${escapeHtml(formatCurrency(breakdown.food))}</div>
        <div class="budget-item"><strong>Activities</strong><br>${escapeHtml(formatCurrency(breakdown.activities))}</div>
        <div class="budget-item"><strong>Miscellaneous</strong><br>${escapeHtml(formatCurrency(breakdown.miscellaneous))}</div>
        <div class="budget-item"><strong>Total Estimated Cost</strong><br>${escapeHtml(formatCurrency(budget.estimated_cost))}</div>
      </div>
    </section>
    <section class="section">
      <h2>Complete Itinerary</h2>
      ${daysHtml || "<p>No day-by-day itinerary was provided.</p>"}
    </section>
    <section class="section">
      <h2>Important Notes</h2>
      ${
        Array.isArray(itinerary.important_notes) && itinerary.important_notes.length
          ? `<ul>${listHtml(itinerary.important_notes)}</ul>`
          : "<p>No additional itinerary notes.</p>"
      }
    </section>
    <section class="section">
      <h2>Trip Validation</h2>
      <p><span class="status">${escapeHtml(validation.status || "VALID")}</span></p>
      <p>${escapeHtml(validation.message || "Your travel plan has passed the available validation checks.")}</p>
      ${notes.length ? `<ul>${listHtml(notes)}</ul>` : ""}
    </section>
    <footer class="footer">Generated by TripGenie AI<br>AI-powered personalized travel planning</footer>
  </main>
</body>
</html>`;

    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const destination =
      trip.destination?.replace(/[^a-z0-9]/gi, "-") || "Trip";

    link.href = url;
    link.download = `TripGenie-${destination}-Travel-Plan.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const downloadTripPDF = async () => {
    if (!result) return;

    setIsGeneratingPDF(true);
    setError("");

    try {
      const { default: jsPDF } = await import("jspdf");

      const pdf = new jsPDF("p", "mm", "a4");
      pdf.setFont("helvetica", "normal");

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 16;
      const contentWidth = pageWidth - margin * 2;
      const breakdown = budget.breakdown || {};
      const places = Array.isArray(research.recommended_places)
        ? research.recommended_places
        : [];
      const notes = Array.isArray(validation.notes)
        ? validation.notes
        : Array.isArray(validation.issues)
          ? validation.issues
          : [];
      let y = 20;

      const clean = (value) => String(value ?? "").trim();
      const pdfCurrency = (value) =>
        formatCurrency(value).replace(/₹/g, "Rs. ");
    const checkPage = (needed = 15) => {
      if (y + needed > pageHeight - 18) {
        pdf.addPage();
        y = 20;
      }
    };
    const addWrappedText = (
      text,
      x,
      width,
      fontSize = 10,
      lineHeight = 5
    ) => {
      pdf.setFontSize(fontSize);
      const lines = pdf.splitTextToSize(clean(text), width);

      lines.forEach((line) => {
        checkPage(lineHeight);
        pdf.text(line, x, y);
        y += lineHeight;
      });

      return y;
    };
    const addSectionHeading = (text, fontSize = 16) => {
      checkPage(18);
      pdf.setTextColor(23, 61, 45);
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(fontSize);
      pdf.text(clean(text), margin, y);
      y += 9;
    };

    pdf.setFillColor(23, 61, 45);
    pdf.rect(0, 0, pageWidth, 48, "F");
    pdf.setTextColor(255, 255, 255);
    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(11);
    pdf.text("TRIPGENIE AI", margin, 16);
    pdf.setFontSize(25);
    pdf.text(clean(trip.destination || "Travel Plan").slice(0, 42), margin, 30);
    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(10);
    pdf.text("AI-Powered Personalized Travel Plan", margin, 39);
    y = 62;

    addSectionHeading("Trip Summary");
    const summary = [
      ["Destination", trip.destination],
      ["Duration", trip.duration],
      ["Travelers", trip.travelers],
      ["Budget", pdfCurrency(trip.budget)],
    ];
    const boxWidth = (contentWidth - 9) / 2;
    const boxHeight = 20;

    summary.forEach(([label, value], index) => {
      const col = index % 2;
      const row = Math.floor(index / 2);
      const x = margin + col * (boxWidth + 9);
      const boxY = y + row * (boxHeight + 7);

      pdf.setFillColor(245, 249, 246);
      pdf.roundedRect(x, boxY, boxWidth, boxHeight, 3, 3, "F");
      pdf.setTextColor(113, 133, 124);
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(8);
      pdf.text(clean(label.toUpperCase()), x + 5, boxY + 7);
      pdf.setTextColor(23, 53, 42);
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(10);
      pdf.text(clean(value || "Not specified").slice(0, 38), x + 5, boxY + 14);
    });

    y += 2 * (boxHeight + 7) + 8;
    addSectionHeading("Trip Overview");
    pdf.setTextColor(55, 65, 81);
    pdf.setFont("helvetica", "normal");
    addWrappedText(
      research.destination_overview ||
        "Personalized travel plan generated by TripGenie AI.",
      margin,
      contentWidth,
      10,
      5
    );
    y += 7;

    addSectionHeading("Budget Analysis");
    const budgetRows = [
      ["Accommodation", breakdown.accommodation],
      ["Transportation", breakdown.transportation],
      ["Food", breakdown.food],
      ["Activities", breakdown.activities],
      ["Miscellaneous", breakdown.miscellaneous],
      ["Total Estimated Cost", budget.estimated_cost],
    ];

    budgetRows.forEach(([label, value]) => {
      checkPage(9);
      pdf.setTextColor(55, 65, 81);
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(10);
      pdf.text(clean(label), margin, y);
      pdf.setFont("helvetica", "bold");
      pdf.text(pdfCurrency(value), pageWidth - margin, y, { align: "right" });
      pdf.setDrawColor(226, 234, 228);
      pdf.line(margin, y + 2, pageWidth - margin, y + 2);
      y += 8;
    });
    y += 5;

    addSectionHeading("Recommended Places");
    if (places.length === 0) {
      pdf.setTextColor(75, 85, 99);
      pdf.setFont("helvetica", "normal");
      addWrappedText("No recommended places were provided.", margin, contentWidth);
    }
    places.forEach((place) => {
      checkPage(14);
      pdf.setTextColor(35, 77, 58);
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(10);
      addWrappedText(
        `${place.name || "Recommended place"}${place.category ? ` - ${place.category}` : ""}`,
        margin,
        contentWidth,
        10,
        5
      );
      pdf.setTextColor(75, 85, 99);
      pdf.setFont("helvetica", "normal");
      addWrappedText(place.description || "", margin, contentWidth, 9, 4.5);
      y += 3;
    });

    y += 3;
    addSectionHeading("Complete Itinerary", 18);
    days.forEach((day) => {
      checkPage(25);
      pdf.setFillColor(237, 245, 239);
      pdf.roundedRect(margin, y - 5, contentWidth, 12, 3, 3, "F");
      pdf.setTextColor(53, 112, 82);
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(9);
      pdf.text(`DAY ${clean(day.day)}`, margin + 5, y + 3);
      y += 13;
      pdf.setTextColor(23, 53, 42);
      pdf.setFont("helvetica", "bold");
      addWrappedText(day.title || `Day ${day.day}`, margin, contentWidth, 12, 5.5);
      y += 2;

      const sections = [
        ["Morning", day.morning],
        ["Afternoon", day.afternoon],
        ["Evening", day.evening],
        ["Meals", day.meals],
      ];

      sections.forEach(([title, items]) => {
        if (!Array.isArray(items) || items.length === 0) return;

        checkPage(11);
        pdf.setTextColor(55, 77, 64);
        pdf.setFont("helvetica", "bold");
        pdf.setFontSize(10);
        pdf.text(title, margin, y);
        y += 5;
        pdf.setTextColor(75, 85, 99);
        pdf.setFont("helvetica", "normal");
        items.forEach((item) => {
          addWrappedText(`- ${item}`, margin + 3, contentWidth - 3, 9, 4.5);
          y += 1;
        });
        y += 2;
      });

      if (day.estimated_daily_cost !== undefined) {
        checkPage(9);
        pdf.setTextColor(53, 112, 82);
        pdf.setFont("helvetica", "bold");
        pdf.setFontSize(9);
        pdf.text(
          `Estimated Daily Cost: ${pdfCurrency(day.estimated_daily_cost)}`,
          margin,
          y
        );
        y += 7;
      }

      if (day.notes) {
        pdf.setTextColor(100, 116, 139);
        pdf.setFont("helvetica", "normal");
        addWrappedText(`Notes: ${day.notes}`, margin, contentWidth, 9, 4.5);
        y += 4;
      }
      y += 5;
    });

    y += 3;
    addSectionHeading("Important Notes");
    const importantNotes = Array.isArray(itinerary.important_notes)
      ? itinerary.important_notes
      : [];
    if (importantNotes.length === 0) {
      pdf.setTextColor(75, 85, 99);
      pdf.setFont("helvetica", "normal");
      addWrappedText("No additional itinerary notes.", margin, contentWidth, 9, 5);
    }
    importantNotes.forEach((note) => {
      addWrappedText(`- ${note}`, margin, contentWidth, 9, 5);
      y += 1;
    });

    y += 4;
    addSectionHeading("Trip Validation");
    pdf.setTextColor(53, 112, 82);
    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(11);
    addWrappedText(validation.status || "VALID", margin, contentWidth, 11, 5);
    pdf.setTextColor(75, 85, 99);
    pdf.setFont("helvetica", "normal");
    addWrappedText(
      validation.message || "Trip plan validation completed.",
      margin,
      contentWidth,
      9,
      5
    );
    notes.forEach((note) => {
      addWrappedText(`- ${note}`, margin, contentWidth, 9, 5);
    });

    const totalPages = pdf.internal.getNumberOfPages();
    for (let page = 1; page <= totalPages; page += 1) {
      pdf.setPage(page);
      pdf.setDrawColor(226, 234, 228);
      pdf.line(margin, pageHeight - 12, pageWidth - margin, pageHeight - 12);
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(7);
      pdf.setTextColor(100, 116, 139);
      pdf.text("Generated by TripGenie AI", margin, pageHeight - 7);
      pdf.text(`Page ${page} of ${totalPages}`, pageWidth - margin, pageHeight - 7, {
        align: "right",
      });
    }

    const destination =
      trip.destination?.replace(/[^a-z0-9]/gi, "-") || "Trip";
    pdf.save(`TripGenie-${destination}-Travel-Plan.pdf`);
    } catch (error) {
      console.error("PDF generation failed:", error);
      setError("Unable to generate the PDF. Please try again.");
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  return (
    <div
      className="app-shell"
      style={{ "--backdrop-img": `url("${backdropImage}")` }}
    >
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">✈</div>

          <div>
            <div className="brand-name">TripGenie AI</div>
            <div className="brand-tagline">
              Your intelligent AI travel agent
            </div>
          </div>
        </div>

        {result && (
          <button className="secondary-button" onClick={planAnotherTrip}>
            + New Trip
          </button>
        )}
      </header>

      {!result && (
        <main className="hero-section">
          <div className="hero-badge">
            <span className="pulse-dot" />
            Agentic AI Travel Planner
          </div>

          <h1>
            Plan your next journey
            <br />
            <span>with AI.</span>
          </h1>

          <p className="hero-description">
            Tell TripGenie where you want to go, your budget,
            interests and travel preferences. Our AI agents work
            together to build a personalized travel plan.
          </p>

          <div className="planner-card">
            <div className="input-label">
              <span>✦</span>
              Where would you like to go?
            </div>

            <textarea
              value={request}
              onChange={(event) => {
                setRequest(event.target.value);
                setError("");
              }}
              placeholder={exampleRequest}
              rows={5}
              disabled={loading}
            />

            <div className="planner-footer">
              <button
                className="example-button"
                onClick={useExample}
                disabled={loading}
              >
                Try an example
              </button>

              <button
                className="primary-button rounded-full"
                onClick={startPlanning}
                disabled={loading || !request.trim()}
              >
                {loading ? (
                  <>
                    <span className="button-spinner" />
                    Planning...
                  </>
                ) : (
                  <>
                    Plan My Trip
                    <span>→</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-box">
              <span>⚠</span>
              <div>
                <strong>Something went wrong</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          <div className="feature-row">
            <div>
              <span>🤖</span>
              Multi-Agent AI
            </div>

            <div>
              <span>💰</span>
              Smart Budgeting
            </div>

            <div>
              <span>🗓️</span>
              Personalized Itinerary
            </div>

            <div>
              <span>✓</span>
              Plan Validation
            </div>
          </div>
        </main>
      )}

      {loading && !result && (
        <section className="processing-section">
          <div className="processing-card">
            <div className="processing-header">
              <div className="processing-orb">✦</div>
              <div>
                <h2>TripGenie AI is planning your trip</h2>
                <p>
                  Multiple AI agents are working together to create your plan.
                </p>
              </div>
            </div>

            <div className="agent-progress">
              {planningAgents.map((agent, index) => {
                const status = getAgentStatus(agent.name);
                const active = status === "active";

                return (
                  <div
                    className={`progress-agent ${status}`}
                    key={agent.name}
                  >
                    <div className="progress-icon">
                      {status === "completed"
                        ? "✓"
                        : active
                          ? "●"
                          : index + 1}
                    </div>

                    <div className="progress-content">
                      <strong>{agent.name}</strong>
                      <span>{
                        agentMessages[agent.name] ||
                        (status === "waiting" ? "Waiting..." : agent.description)
                      }</span>
                      {agentTimes[agent.name] && (
                        <small>{agentTimes[agent.name]}s</small>
                      )}
                    </div>

                    {active && (
                      <div className="agent-loader" aria-label="In progress">
                        <span />
                        <span />
                        <span />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="processing-footer" aria-live="polite">
              <span className="pulse-dot" />
              {activeAgent
                ? `${activeAgent} is working on your travel plan...`
                : "AI agents are collaborating on your travel plan..."}
            </div>
          </div>
        </section>
      )}

      {result && (
        <main className="results-page">
          <section className="trip-hero">
            <div className="trip-hero-content">
              <div className="result-label">
                YOUR AI TRIP PLAN
              </div>

              <h1>{trip.destination || "Your Journey"}</h1>

              <p>
                {trip.duration || "Custom duration"}{" "}
                {trip.travel_dates ? `• ${trip.travel_dates}` : ""}
              </p>

              <div className="trip-pills">
                <span>👥 {trip.travelers || "—"} Travelers</span>
                <span>💳 {trip.budget || "Budget not specified"}</span>
                {trip.starting_location && (
                  <span>📍 From {trip.starting_location}</span>
                )}
              </div>
            </div>

            <div
              className={`validation-badge ${
                validation.status === "VALID" ? "valid" : "review"
              }`}
            >
              <span>{validation.status === "VALID" ? "✓" : "!"}</span>

              <div>
                <small>PLAN STATUS</small>
                <strong>{validation.status || "REVIEW"}</strong>
              </div>
            </div>
          </section>

          <section className="trip-summary-grid">
            <div className="summary-item">
              <span>Destination</span>
              <strong>{trip?.destination || "—"}</strong>
            </div>

            <div className="summary-item">
              <span>Duration</span>
              <strong>{trip?.duration || "—"}</strong>
            </div>

            <div className="summary-item">
              <span>Travelers</span>
              <strong>{trip?.travelers || "—"}</strong>
            </div>

            <div className="summary-item">
              <span>Budget</span>
              <strong>
                {trip?.budget ? formatCurrency(trip.budget) : "Not specified"}
              </strong>
            </div>
          </section>

          <section className="section-card">
            <div className="section-heading">
              <div>
                <span className="section-eyebrow">
                  INTELLIGENT WORKFLOW
                </span>
                <h2>AI Agent Activity</h2>
              </div>

              <span className="live-indicator">
                <span />
                COMPLETED
              </span>
            </div>

            <div className="agent-grid">
              {agents.map((agent, index) => (
                <div
                  className={`agent-item ${statusClass(agent.status)}`}
                  key={`${agent.agent}-${index}`}
                >
                  <div className="agent-icon">
                    {getAgentIcon(agent.agent)}
                  </div>

                  <div className="agent-info">
                    <strong>{agent.agent}</strong>
                    <span>{agent.message}</span>
                  </div>

                  <div className="agent-status">
                    {agent.status === "completed"
                      ? "✓"
                      : agent.status === "running"
                        ? "..."
                        : agent.status === "failed"
                          ? "!"
                          : "○"}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {research.destination_overview && (
            <section className="section-card research-card">
              <div className="section-heading">
                <div>
                  <span className="section-eyebrow">
                    DESTINATION RESEARCH
                  </span>
                  <h2>Discover {trip.destination}</h2>
                </div>
              </div>

              <p className="overview-text">
                {research.destination_overview}
              </p>
            </section>
          )}

          {Array.isArray(research.recommended_activities) &&
            research.recommended_activities.length > 0 && (
              <section className="highlights-section">
                <div className="section-heading">
                  <span className="section-kicker">AI CURATED</span>
                  <h2>Trip Highlights</h2>
                  <p>
                    Personalized experiences selected by your AI travel team.
                  </p>
                </div>

                <div className="highlights-grid">
                  {research.recommended_activities
                    .slice(0, 6)
                    .map((activity, index) => (
                      <div className="highlight-card" key={index}>
                        <div className="highlight-number">
                          {String(index + 1).padStart(2, "0")}
                        </div>

                        <div>
                          <h3>
                            {typeof activity === "string"
                              ? activity
                              : activity.name ||
                                activity.title ||
                                "Recommended activity"}
                          </h3>
                          <p>
                            Recommended based on your travel preferences.
                          </p>
                        </div>
                      </div>
                    ))}
                </div>
              </section>
            )}

          {Array.isArray(research.recommended_places) &&
            research.recommended_places.length > 0 && (
              <section className="section-card places-section">
                <div className="section-heading">
                  <div>
                    <span className="section-eyebrow">
                      DESTINATION RESEARCH
                    </span>
                    <h2>Recommended Places</h2>
                  </div>
                </div>

                <div className="recommendation-grid">
                  {research.recommended_places.map((place, index) => (
                    <div
                      className="recommendation-card"
                      key={`${place.name}-${index}`}
                    >
                      <span className="recommendation-number">
                        {String(index + 1).padStart(2, "0")}
                      </span>

                      <div>
                        <small>{place.category}</small>
                        <h3>{place.name}</h3>
                        <p>{place.description}</p>

                        {place.estimated_cost && (
                          <strong>{place.estimated_cost}</strong>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

          {budget && (
            <section className="budget-section">
              <div className="section-heading">
                <span className="section-kicker">AI BUDGET ANALYSIS</span>
                <h2>Trip Budget</h2>
                <p>Estimated spending based on your travel plan.</p>
              </div>

              <div className="budget-overview">
                <div className="budget-total">
                  <span>Your Budget</span>
                  <strong>
                    {budget.budget_limit
                      ? formatCurrency(budget.budget_limit)
                      : "Not specified"}
                  </strong>
                </div>

                <div className="budget-total">
                  <span>Estimated Cost</span>
                  <strong>
                    {formatCurrency(budget.estimated_cost || 0)}
                  </strong>
                </div>

                <div className="budget-total">
                  <span>Remaining</span>
                  <strong>
                    {formatCurrency(
                      Math.max(budget.remaining_budget || 0, 0)
                    )}
                  </strong>
                </div>
              </div>

              {budget.breakdown && (
                <div className="budget-breakdown">
                  {Object.entries(budget.breakdown).map(([category, amount]) => (
                    <div className="budget-row" key={category}>
                      <div className="budget-category">
                        <span
                          className={`budget-dot ${category.toLowerCase()}`}
                        />
                        <span>
                          {category.charAt(0).toUpperCase() + category.slice(1)}
                        </span>
                      </div>

                      <strong>{formatCurrency(amount || 0)}</strong>
                    </div>
                  ))}
                </div>
              )}

              {budget.status && (
                <div
                  className={`budget-status ${budget.status.toLowerCase()}`}
                >
                  <span>
                    {budget.status === "WITHIN_BUDGET"
                      ? "✓"
                      : budget.status === "OVER_BUDGET"
                        ? "!"
                        : "•"}
                  </span>

                  <div>
                    <strong>
                      {budget.status === "WITHIN_BUDGET"
                        ? "Within Budget"
                        : budget.status === "OVER_BUDGET"
                          ? "Over Budget"
                          : "Budget Status"}
                    </strong>

                    <p>
                      {budget.status === "WITHIN_BUDGET"
                        ? "Your estimated trip cost fits within the specified budget."
                        : budget.status === "OVER_BUDGET"
                          ? "The estimated trip cost exceeds the specified budget."
                          : "Budget information requires further review."}
                    </p>
                  </div>
                </div>
              )}

              {Array.isArray(budget.recommendations) &&
                budget.recommendations.length > 0 && (
                  <div className="budget-recommendations">
                    <h3>Budget Recommendations</h3>

                    <ul>
                      {budget.recommendations.map((recommendation, index) => (
                        <li key={index}>
                          {typeof recommendation === "string"
                            ? recommendation
                            : recommendation?.text ||
                              recommendation?.description ||
                              JSON.stringify(recommendation)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
            </section>
          )}

          <section className="section-card itinerary-section">
            <div className="section-heading">
              <div>
                <span className="section-eyebrow">
                  PERSONALIZED SCHEDULE
                </span>
                <h2>Your {days.length}-Day Itinerary</h2>
              </div>

              <span className="days-count">{days.length} DAYS</span>
            </div>

            <div className="itinerary-list">
              {days.map((day) => (
                <article className="day-card" key={day.day}>
                  <div className="day-card-header">
                    <div className="day-badge">
                      <span>DAY</span>
                      <strong>{day.day}</strong>
                    </div>

                    <div className="day-title">
                      <h3>{day.title || `Day ${day.day}`}</h3>
                      {day.notes && <p>{day.notes}</p>}
                    </div>

                    {day.estimated_daily_cost !== undefined && (
                      <div className="day-cost">
                        <span>Estimated</span>
                        <strong>{formatCurrency(day.estimated_daily_cost)}</strong>
                      </div>
                    )}
                  </div>

                  <div className="day-timeline">
                    {[
                      ["Morning", day.morning, "🌅", "No morning activities planned."],
                      ["Afternoon", day.afternoon, "☀️", "No afternoon activities planned."],
                      ["Evening", day.evening, "🌙", "No evening activities planned."],
                    ].map(([period, activities, icon, emptyMessage]) => (
                      <div className="timeline-section" key={period}>
                        <div className="timeline-icon">{icon}</div>
                        <div className="timeline-content">
                          <span className="timeline-label">{period}</span>
                          {Array.isArray(activities) && activities.length > 0 ? (
                            <ul>
                              {activities.map((item, index) => (
                                <li key={index}>
                                  {formatItineraryActivity(item)}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="empty-activity">{emptyMessage}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {Array.isArray(day.meals) && day.meals.length > 0 && (
                    <div className="day-meals">
                      <span>🍽️ Meals</span>
                      <div>
                        {day.meals.map((meal, index) => (
                          <span className="meal-chip" key={index}>
                            {typeof meal === "string"
                              ? meal
                              : meal?.name || meal?.title || "Meal"}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </article>
              ))}
            </div>
          </section>

          {validation && (
            <section
              className={`validation-card validation-${String(
                validation.status || ""
              ).toLowerCase()}`}
            >
              <div className="validation-header">
                <div className="validation-icon">
                  {validation.status === "VALID"
                    ? "✓"
                    : validation.status === "NEEDS_REVIEW"
                      ? "!"
                      : "×"}
                </div>

                <div>
                  <span className="section-kicker">PLAN VALIDATION</span>

                  <h2>
                    {validation.status === "VALID"
                      ? "Your travel plan is ready"
                      : validation.status === "NEEDS_REVIEW"
                        ? "Your travel plan needs review"
                        : "Your travel plan needs attention"}
                  </h2>

                  <p>
                    {validation.status === "VALID"
                      ? "All required trip details and itinerary checks have passed."
                      : validation.status === "NEEDS_REVIEW"
                        ? "A few items should be checked before relying on this itinerary."
                        : "One or more checks require attention before using this plan."}
                  </p>
                </div>
              </div>

              {Array.isArray(validation.issues) &&
                validation.issues.length > 0 && (
                  <div className="validation-issues">
                    <h3>Items to Review</h3>

                    <ul>
                      {validation.issues.map((issue, index) => (
                        <li key={index}>
                          <span>!</span>

                          <div>
                            {typeof issue === "string"
                              ? issue
                              : issue?.message ||
                                issue?.description ||
                                issue?.issue ||
                                JSON.stringify(issue)}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {Array.isArray(validation.checks) &&
                validation.checks.length > 0 && (
                  <div className="validation-checks">
                    <h3>Validation Checks</h3>

                    {validation.checks.map((check, index) => (
                      <div className="validation-check" key={index}>
                        <span>
                          {typeof check !== "string" && check.passed === false
                            ? "!"
                            : "✓"}
                        </span>

                        <div>
                          <strong>
                            {typeof check === "string"
                              ? check
                              : check.name || check.check || "Validation check"}
                          </strong>

                          {typeof check !== "string" && check.message && (
                            <p>{check.message}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
            </section>
          )}

          <div className="results-actions">
            {error && (
              <div className="error-box" role="alert">
                <span>⚠</span>
                <div>
                  <strong>PDF generation failed</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}
            <button
              className="download-btn"
              onClick={downloadTripPDF}
              disabled={isGeneratingPDF}
            >
              {isGeneratingPDF ? "Generating PDF..." : "↓ Download PDF"}
            </button>
            <button className="primary-button large" onClick={planAnotherTrip}>
              ✦ Plan Another Trip
            </button>
          </div>
        </main>
      )}

      <footer className="app-footer">
        <strong>TripGenie AI</strong>
        <span>Powered by intelligent multi-agent AI</span>
      </footer>
    </div>
  );
}

export default App;
