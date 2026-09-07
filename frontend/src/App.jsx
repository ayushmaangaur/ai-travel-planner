import { useState } from "react";
import "./App.css";

function App() {
  const emptyForm = {
    current_location: "",
    origin: "",
    destination: "",
    days: "",
    budget: "",
    travelers: "",
    preference: "",
    start_date: "",
  };

  const [form, setForm] = useState(emptyForm);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      type: "text",
      content:
        "Hi! 👋 I'm your AI Travel Planner. Tell me a few details about your trip and I'll build the plan for you.",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const updateField = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSameOrigin = (checked) => {
    setForm((prev) => ({
      ...prev,
      origin: checked ? prev.current_location : "",
    }));
  };

  const handleCurrentLocationChange = (value) => {
    setForm((prev) => ({
      ...prev,
      current_location: value,
      origin:
        prev.origin === prev.current_location
          ? value
          : prev.origin,
    }));
  };

  const isFormComplete =
    form.current_location.trim() &&
    form.origin.trim() &&
    form.destination.trim() &&
    form.days &&
    form.budget &&
    form.travelers &&
    form.start_date;

  const formatTravelPlan = (plan) => {
    let text = "";

    if (plan.destination) {
      text += `✈️ Your trip to ${plan.destination} is ready!\n\n`;
    }

    if (plan.itinerary?.length) {
      text += `🗓️ ${plan.itinerary.length}-day itinerary created.\n\n`;
    }

    text += "✈️ Flights: ";
    text +=
      plan.flight_status === "available"
        ? "Available\n"
        : "Currently unavailable\n";

    text += "🏨 Hotels: ";
    text +=
      plan.hotel_status === "available"
        ? "Available\n"
        : "Currently unavailable\n";

    text += "🌤️ Weather: ";
    text +=
      plan.weather_status === "available"
        ? "Available\n"
        : "Currently unavailable\n";

    if (plan.errors?.length) {
      text +=
        "\n⚠️ Some services were unavailable, but I've still prepared the available parts of your trip.";
    }

    return text;
  };

  const planTrip = async () => {
    if (!isFormComplete || loading) return;

    setSubmitted(true);
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        type: "summary",
        content: "Build my trip",
        form: { ...form },
      },
      {
        role: "assistant",
        type: "text",
        content:
          "Perfect ✈️ I have everything I need. Let me build your trip...",
      },
    ]);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/travel/plan",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            current_location: form.current_location,
            origin: form.origin,
            destination: form.destination,
            days: Number(form.days),
            budget: Number(form.budget),
            travelers: Number(form.travelers),
            preference: form.preference || null,
            start_date: form.start_date,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Server error");
      }

      const data = await response.json();

      let plan = null;

      if (data.type === "plan" && data.plan) {
        plan = data.plan;
      } else if (data.destination || data.itinerary) {
        plan = data;
      }

      if (data.type === "message") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            type: "text",
            content: data.message,
          },
        ]);
      } else if (plan) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            type: "plan",
            content: formatTravelPlan(plan),
            plan: plan,
          },
        ]);
      } else {
        throw new Error("Unexpected server response");
      }
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "text",
          content:
            "Sorry, something went wrong while creating your trip. Please make sure the FastAPI server is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const resetPlanner = () => {
    setForm(emptyForm);
    setSubmitted(false);

    setMessages([
      {
        role: "assistant",
        type: "text",
        content:
          "Let's plan another adventure ✈️ Fill in your trip details below.",
      },
    ]);
  };

  const renderActivities = (activities) => {
    if (!activities?.length) {
      return (
        <div className="empty-activities">
          No activities planned.
        </div>
      );
    }

    return activities.map((activity, index) => (
      <div className="activity" key={index}>
        <div className="activity-main">
          <div className="activity-title">
            {activity.name}
          </div>

          {activity.description && (
            <div className="activity-description">
              {activity.description}
            </div>
          )}

          <div className="activity-meta">
            {activity.location && (
              <span>📍 {activity.location}</span>
            )}

            {activity.duration && (
              <span>⏱️ {activity.duration}</span>
            )}

            {activity.estimated_cost !== null &&
              activity.estimated_cost !== undefined && (
                <span>
                  💰 {activity.currency || "INR"}{" "}
                  {activity.estimated_cost}
                </span>
              )}
          </div>
        </div>
      </div>
    ));
  };

  const renderDay = (day) => {
    return (
      <div className="day-card" key={day.day}>
        <div className="day-header">
          <div className="day-number">
            Day {day.day}
          </div>

          <div className="day-heading">
            <h3>{day.title}</h3>
            <p>{day.summary}</p>
          </div>
        </div>

        <div className="day-sections">
          <div className="time-section">
            <div className="time-header">
              <span className="time-icon">🌅</span>
              <span>Morning</span>
            </div>

            <div className="activities">
              {renderActivities(day.morning)}
            </div>
          </div>

          <div className="time-section">
            <div className="time-header">
              <span className="time-icon">☀️</span>
              <span>Afternoon</span>
            </div>

            <div className="activities">
              {renderActivities(day.afternoon)}
            </div>
          </div>

          <div className="time-section">
            <div className="time-header">
              <span className="time-icon">🌆</span>
              <span>Evening</span>
            </div>

            <div className="activities">
              {renderActivities(day.evening)}
            </div>
          </div>
        </div>

        {day.meals?.length > 0 && (
          <div className="day-extra">
            <div className="extra-title">🍴 Meals</div>

            <ul>
              {day.meals.map((meal, index) => (
                <li key={index}>{meal}</li>
              ))}
            </ul>
          </div>
        )}

        {day.travel_tips?.length > 0 && (
          <div className="day-extra">
            <div className="extra-title">
              🚕 Travel tips
            </div>

            <ul>
              {day.travel_tips.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>
        )}

        {day.weather_note && (
          <div className="weather-note">
            <span>🌤️</span>
            <span>{day.weather_note}</span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="app">
      <div className="chat-container">

        {/* HEADER */}
        <header className="header">
          <div>
            <h1>Travel Planner</h1>
            <p>Your AI trip planning assistant</p>
          </div>

          <div className="status">
            <span></span>
            AI Online
          </div>
        </header>

        {/* CHAT */}
        <main className="messages">

          {messages.map((message, index) => (
            <div
              key={index}
              className={`message-row ${message.role}`}
            >
              <div className="avatar">
                {message.role === "assistant" ? "✈️" : "👤"}
              </div>

              <div className="message-wrapper">

                <div className={`message ${message.type}`}>

                  {message.type === "summary" ? (
                    <>
                      <strong>
                        Trip details submitted ✈️
                      </strong>

                      <div className="submitted-summary">
                        <span>
                          📍 {message.form.current_location}
                        </span>

                        <span>
                          🌍 {message.form.destination}
                        </span>

                        <span>
                          📅 {message.form.days} days
                        </span>

                        <span>
                          👥 {message.form.travelers} travellers
                        </span>

                        <span>
                          💰 ₹{message.form.budget}
                        </span>

                        <span>
                          🗓️ {message.form.start_date}
                        </span>
                      </div>
                    </>
                  ) : (
                    message.content
                      .split("\n")
                      .map((line, i) => (
                        <div key={i}>
                          {line || <br />}
                        </div>
                      ))
                  )}

                </div>

                {/* STRUCTURED TRAVEL PLAN */}
                {message.type === "plan" &&
                  message.plan && (
                    <div className="plan-details">

                      {/* TRIP OVERVIEW */}
                      <div className="overview-card">
                        <div className="overview-title">
                          ✨ Trip overview
                        </div>

                        <div className="overview-grid">
                          <div>
                            <span>Destination</span>
                            <strong>
                              {message.plan.destination}
                            </strong>
                          </div>

                          <div>
                            <span>Flights</span>
                            <strong>
                              {message.plan.flight_status ===
                              "available"
                                ? "Available"
                                : "Unavailable"}
                            </strong>
                          </div>

                          <div>
                            <span>Hotels</span>
                            <strong>
                              {message.plan.hotel_status ===
                              "available"
                                ? "Available"
                                : "Unavailable"}
                            </strong>
                          </div>

                          <div>
                            <span>Weather</span>
                            <strong>
                              {message.plan.weather_status ===
                              "available"
                                ? "Available"
                                : "Unavailable"}
                            </strong>
                          </div>
                        </div>
                      </div>

                      {/* ITINERARY */}
                      {message.plan.itinerary?.length > 0 && (
                        <div className="itinerary-section">
                          <div className="section-heading">
                            <div>
                              <h2>🗓️ Your itinerary</h2>
                              <p>
                                A day-by-day plan built around
                                your trip requirements.
                              </p>
                            </div>
                          </div>

                          <div className="days">
                            {message.plan.itinerary.map(
                              renderDay
                            )}
                          </div>
                        </div>
                      )}

                      {/* FLIGHTS */}
                      {message.plan.flights?.options?.length >
                        0 && (
                        <div className="result-card">
                          <div className="result-card-title">
                            ✈️ Flight options
                          </div>

                          {message.plan.flights.options.map(
                            (flight, i) => (
                              <div
                                className="result-item"
                                key={i}
                              >
                                <div className="result-main">
                                  <strong>
                                    {flight.airline}
                                  </strong>

                                  {flight.flight_number && (
                                    <span>
                                      {flight.flight_number}
                                    </span>
                                  )}
                                </div>

                                <span>
                                  {flight.departure_airport}{" "}
                                  →{" "}
                                  {flight.arrival_airport}
                                </span>

                                {flight.departure_time && (
                                  <span>
                                    🕐{" "}
                                    {flight.departure_time}
                                  </span>
                                )}

                                <span className="result-price">
                                  ₹{flight.price}
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      )}

                      {/* HOTELS */}
                      {message.plan.hotels?.options?.length >
                        0 && (
                        <div className="result-card">
                          <div className="result-card-title">
                            🏨 Hotel options
                          </div>

                          {message.plan.hotels.options.map(
                            (hotel, i) => (
                              <div
                                className="result-item"
                                key={i}
                              >
                                <div className="result-main">
                                  <strong>
                                    {hotel.name}
                                  </strong>

                                  {hotel.location && (
                                    <span>
                                      📍 {hotel.location}
                                    </span>
                                  )}
                                </div>

                                {hotel.rating && (
                                  <span>
                                    ⭐ {hotel.rating}
                                  </span>
                                )}

                                <span className="result-price">
                                  ₹
                                  {
                                    hotel.price_per_night
                                  }
                                  /night
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      )}

                      {/* WEATHER */}
                      {message.plan.weather?.forecast
                        ?.length > 0 && (
                        <div className="result-card">
                          <div className="result-card-title">
                            🌤️ Weather forecast
                          </div>

                          {message.plan.weather.forecast.map(
                            (day, i) => (
                              <div
                                className="result-item"
                                key={i}
                              >
                                <div className="result-main">
                                  <strong>
                                    {day.date}
                                  </strong>
                                </div>

                                <span>
                                  {day.condition}
                                </span>

                                <span>
                                  {day.temperature}
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      )}

                      {/* ERRORS */}
                      {message.plan.errors?.length > 0 && (
                        <div className="error-card">
                          <strong>
                            ⚠️ Some parts of the trip
                            could not be completed
                          </strong>

                          {message.plan.errors.map(
                            (error, index) => (
                              <div key={index}>
                                {error}
                              </div>
                            )
                          )}
                        </div>
                      )}
                    </div>
                  )}

              </div>
            </div>
          ))}

          {/* LOADING */}
          {loading && (
            <div className="message-row assistant">
              <div className="avatar">✈️</div>

              <div className="message typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          {/* TRIP BUILDER */}
          {!submitted && (
            <div className="message-row assistant">
              <div className="avatar">✈️</div>

              <div className="trip-builder">

                <div className="builder-header">
                  <div>
                    <h2>Plan your trip</h2>
                    <p>
                      Fill in the details and I'll handle the
                      rest.
                    </p>
                  </div>

                  <span className="builder-icon">✨</span>
                </div>

                <div className="field-grid">

                  {/* CURRENT LOCATION */}
                  <div className="field-card">
                    <label>
                      📍 Current location
                    </label>

                    <input
                      type="text"
                      placeholder="Mumbai"
                      value={form.current_location}
                      onChange={(e) =>
                        handleCurrentLocationChange(
                          e.target.value
                        )
                      }
                    />
                  </div>

                  {/* ORIGIN */}
                  <div className="field-card">
                    <label>
                      🛫 Starting from
                    </label>

                    <input
                      type="text"
                      placeholder="Mumbai"
                      value={form.origin}
                      onChange={(e) =>
                        updateField(
                          "origin",
                          e.target.value
                        )
                      }
                    />

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        onChange={(e) =>
                          handleSameOrigin(
                            e.target.checked
                          )
                        }
                      />
                      Same as current location
                    </label>
                  </div>

                  {/* DESTINATION */}
                  <div className="field-card destination-card">
                    <label>🌍 Destination</label>

                    <input
                      type="text"
                      placeholder="Tokyo"
                      value={form.destination}
                      onChange={(e) =>
                        updateField(
                          "destination",
                          e.target.value
                        )
                      }
                    />
                  </div>

                  {/* DAYS */}
                  <div className="field-card">
                    <label>📅 Duration</label>

                    <div className="input-with-unit">
                      <input
                        type="number"
                        min="1"
                        placeholder="7"
                        value={form.days}
                        onChange={(e) =>
                          updateField(
                            "days",
                            e.target.value
                          )
                        }
                      />

                      <span>days</span>
                    </div>
                  </div>

                  {/* TRAVELLERS */}
                  <div className="field-card">
                    <label>👥 Travellers</label>

                    <div className="input-with-unit">
                      <input
                        type="number"
                        min="1"
                        placeholder="2"
                        value={form.travelers}
                        onChange={(e) =>
                          updateField(
                            "travelers",
                            e.target.value
                          )
                        }
                      />

                      <span>people</span>
                    </div>
                  </div>

                  {/* BUDGET */}
                  <div className="field-card">
                    <label>💰 Budget</label>

                    <div className="input-with-unit">
                      <span>₹</span>

                      <input
                        type="number"
                        min="0"
                        placeholder="50000"
                        value={form.budget}
                        onChange={(e) =>
                          updateField(
                            "budget",
                            e.target.value
                          )
                        }
                      />
                    </div>
                  </div>

                  {/* DATE */}
                  <div className="field-card">
                    <label>🗓️ Travel date</label>

                    <input
                      type="date"
                      value={form.start_date}
                      onChange={(e) =>
                        updateField(
                          "start_date",
                          e.target.value
                        )
                      }
                    />
                  </div>

                  {/* PREFERENCE */}
                  <div className="field-card">
                    <label>✨ Preference</label>

                    <select
                      value={form.preference}
                      onChange={(e) =>
                        updateField(
                          "preference",
                          e.target.value
                        )
                      }
                    >
                      <option value="">
                        Choose a style
                      </option>

                      <option value="budget-friendly">
                        💸 Budget-friendly
                      </option>

                      <option value="balanced">
                        ⚖️ Balanced
                      </option>

                      <option value="luxury">
                        💎 Luxury
                      </option>

                      <option value="adventure">
                        🏔️ Adventure
                      </option>

                      <option value="relaxed">
                        🌴 Relaxed
                      </option>

                      <option value="cheap flights">
                        ✈️ Cheap flights
                      </option>
                    </select>
                  </div>
                </div>

                <button
                  className="plan-button"
                  onClick={planTrip}
                  disabled={!isFormComplete || loading}
                >
                  <span>✈️</span>
                  {loading
                    ? "Building your trip..."
                    : "Plan my trip"}
                  <span>→</span>
                </button>

                {!isFormComplete && (
                  <p className="required-hint">
                    Fill in the required details to continue
                  </p>
                )}
              </div>
            </div>
          )}

          {/* NEW TRIP */}
          {submitted && !loading && (
            <button
              className="new-trip-button"
              onClick={resetPlanner}
            >
              ✨ Plan another trip
            </button>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;