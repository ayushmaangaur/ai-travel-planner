import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      type: "welcome",
      content:
        "Hi! I'm your AI travel assistant. Tell me where you'd like to go, how long you want to stay, your budget, or anything else you have in mind.",
    },
  ]);

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    const userMessage = message.trim();

    if (!userMessage || loading) {
      return;
    }

    setMessage("");

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userMessage,
      },
    ]);

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/travel/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const data = await response.json();

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          type: "travel-plan",
          plan: data,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          type: "error",
          content:
            "Sorry, I couldn't connect to the travel planner. Please make sure the backend is running and try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">✦</div>

          <div>
            <h1>AI Travel Planner</h1>
            <p>Your personal AI travel assistant</p>
          </div>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.map((item, index) => {
            if (item.type === "travel-plan") {
              return (
                <TravelPlan
                  key={index}
                  plan={item.plan}
                />
              );
            }

            return (
              <div
                key={index}
                className={`message-row ${item.role}`}
              >
                {item.role === "assistant" && (
                  <div className="avatar">✦</div>
                )}

                <div
                  className={`message-bubble ${
                    item.type === "error"
                      ? "error-bubble"
                      : ""
                  }`}
                >
                  {item.content}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="message-row assistant">
              <div className="avatar">✦</div>

              <div className="message-bubble typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        <form
          className="composer"
          onSubmit={handleSubmit}
        >
          <input
            type="text"
            value={message}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            placeholder="Tell me about your trip..."
            disabled={loading}
          />

          <button
            type="submit"
            disabled={loading || !message.trim()}
          >
            {loading ? "..." : "Send"}
          </button>
        </form>

        <p className="disclaimer">
          AI-generated travel recommendations. Always verify
          important travel information before booking.
        </p>
      </main>
    </div>
  );
}


function TravelPlan({ plan }) {
  return (
    <div className="travel-response">
      <div className="message-row assistant">
        <div className="avatar">✦</div>

        <div className="message-bubble">
          Here's your travel plan for{" "}
          <strong>{plan.destination}</strong> ✈️
        </div>
      </div>

      <div className="plan-content">

        <div className="status-card">
          <div className="status-item">
            <span>✈️</span>
            <div>
              <small>Flights</small>
              <strong>{plan.flight_status}</strong>
            </div>
          </div>

          <div className="status-item">
            <span>🏨</span>
            <div>
              <small>Hotels</small>
              <strong>{plan.hotel_status}</strong>
            </div>
          </div>

          <div className="status-item">
            <span>🌤️</span>
            <div>
              <small>Weather</small>
              <strong>{plan.weather_status}</strong>
            </div>
          </div>
        </div>


        <section className="plan-card">
          <div className="card-title">
            <span>📅</span>
            <h3>Your itinerary</h3>
          </div>

          <div className="itinerary">
            {plan.itinerary?.map((day, index) => (
              <div
                className="itinerary-day"
                key={index}
              >
                <div className="day-number">
                  {index + 1}
                </div>

                <div className="day-content">
                  <strong>
                    Day {index + 1}
                  </strong>

                  <p>{cleanDay(day)}</p>
                </div>
              </div>
            ))}
          </div>
        </section>


        {plan.flights && (
          <section className="plan-card">
            <div className="card-title">
              <span>✈️</span>
              <h3>Flights</h3>
            </div>

            <p className="route">
              {plan.flights.origin}
              <span>→</span>
              {plan.flights.destination}
            </p>

            <div className="options">
              {plan.flights.options?.map(
                (flight, index) => (
                  <div
                    className="option"
                    key={index}
                  >
                    <div>
                      <strong>
                        {flight.airline}
                      </strong>

                      {flight.flight_number && (
                        <span className="muted">
                          {" "}
                          • {flight.flight_number}
                        </span>
                      )}

                      <p>
                        {flight.departure_airport} →{" "}
                        {flight.arrival_airport}
                      </p>

                      <small>
                        {flight.departure_time} →{" "}
                        {flight.arrival_time}
                      </small>
                    </div>

                    <strong className="price">
                      ₹{flight.price}
                    </strong>
                  </div>
                )
              )}
            </div>
          </section>
        )}


        {plan.hotels && (
          <section className="plan-card">
            <div className="card-title">
              <span>🏨</span>
              <h3>Hotels</h3>
            </div>

            <div className="options">
              {plan.hotels.options?.map(
                (hotel, index) => (
                  <div
                    className="option hotel"
                    key={index}
                  >
                    <div>
                      <strong>
                        {hotel.name}
                      </strong>

                      <p>
                        📍 {hotel.location}
                      </p>

                      <small>
                        ⭐ {hotel.rating}
                      </small>

                      {hotel.amenities?.length > 0 && (
                        <div className="amenities">
                          {hotel.amenities.map(
                            (amenity, i) => (
                              <span key={i}>
                                {amenity}
                              </span>
                            )
                          )}
                        </div>
                      )}
                    </div>

                    <strong className="price">
                      ₹{hotel.price_per_night}
                      <small>/night</small>
                    </strong>
                  </div>
                )
              )}
            </div>
          </section>
        )}


        {plan.weather && (
          <section className="plan-card">
            <div className="card-title">
              <span>🌤️</span>
              <h3>Weather</h3>
            </div>

            <div className="weather-grid">
              {plan.weather.forecast?.map(
                (day, index) => (
                  <div
                    className="weather-day"
                    key={index}
                  >
                    <strong>{day.date}</strong>

                    <div className="weather-condition">
                      {day.condition}
                    </div>

                    <div className="temperature">
                      {day.temperature}
                    </div>

                    <small>
                      🌧️ {day.precipitation}
                    </small>
                  </div>
                )
              )}
            </div>
          </section>
        )}


        {plan.errors?.length > 0 && (
          <section className="warning-card">
            <strong>
              Some travel services were unavailable
            </strong>

            {plan.errors.map((error, index) => (
              <p key={index}>{error}</p>
            ))}
          </section>
        )}

      </div>
    </div>
  );
}


function cleanDay(day) {
  if (!day) {
    return "";
  }

  return day.replace(/^Day\s+\d+:\s*/i, "");
}


export default App;