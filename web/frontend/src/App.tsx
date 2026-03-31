import { useMemo, useState } from "react";

const RANKS = ["A", "4", "5", "6", "7", "S", "C", "R"] as const;
type Rank = (typeof RANKS)[number];

type Probabilities = {
  my_pos: number;
  partner_pos: number;
  p_grande_win: number;
  p_chica_win: number;
  p_pares_reached: number;
  p_pares_win_given_reached: number;
  p_pares_win: number;
  p_juego_reached: number;
  p_juego_win_given_reached: number;
  p_juego_win: number;
  p_punto_reached: number;
  p_punto_win_given_reached: number;
  p_punto_win: number;
  total_weight: number;
};

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function pct(x: number) {
  return `${(x * 100).toFixed(2)}%`;
}

function partnerPos(pos: number) {
  return (pos + 2) % 4;
}

function rankLabel(rank: Rank) {
  if (rank === "S") return "Sota";
  if (rank === "C") return "Caballo";
  if (rank === "R") return "Rey/3";
  if (rank === "A") return "As/2";
  return rank;
}

function CardPicker({
  label,
  value,
  onChange,
}: {
  label: string;
  value: Rank;
  onChange: (v: Rank) => void;
}) {
  return (
    <div className="card-slot">
      <div className="card-label">{label}</div>
      <div className="playing-card">
        <div className="playing-card-top">{value}</div>
        <div className="playing-card-center">{value}</div>
        <select
          className="card-select"
          value={value}
          onChange={(e) => onChange(e.target.value as Rank)}
        >
          {RANKS.map((r) => (
            <option key={r} value={r}>
              {r} · {rankLabel(r)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

function MetricBox({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <div className="metric-box">
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
    </div>
  );
}

export default function App() {
  const [myPos, setMyPos] = useState("0");
  const [myCards, setMyCards] = useState<Rank[]>(["R", "R", "7", "A"]);
  const [partnerCards, setPartnerCards] = useState<Rank[]>(["A", "A", "S", "C"]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Probabilities | null>(null);

  const myPosNum = Number(myPos);
  const partner = useMemo(() => partnerPos(myPosNum), [myPosNum]);

  async function handleCalculate() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          my_pos: myPosNum,
          my_cards: myCards,
          partner_cards: partnerCards
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "No se pudo consultar la API");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setMyPos("0");
    setMyCards(["R", "R", "7", "A"]);
    setPartnerCards(["A", "A", "S", "C"]);
    setResult(null);
    setError(null);
  }

  return (
    <div className="page">
      <div className="container">
        <header className="hero">
          <div>
            <div className="eyebrow">OrdagoSimulator</div>
            <h1>Calculador de probabilidades a cartas dadas</h1>
            <p>
              Selecciona tu posición y las ocho cartas conocidas de la pareja.
              La web consulta la tabla maestra exacta y devuelve probabilidades
              instantáneas para grande, chica, pares, juego y punto.
            </p>
          </div>

          <div className="hero-actions">
            <button className="primary-btn" onClick={handleCalculate} disabled={loading}>
              {loading ? "Consultando…" : "Calcular probabilidades"}
            </button>
            <button className="secondary-btn" onClick={handleReset}>
              Reiniciar
            </button>
          </div>
        </header>

        <section className="table-layout">
          <aside className="side-panel">
            <div className="side-title">Selecciona tu posición</div>
            <div className="side-pos">{myPosNum}</div>
            <div className="side-partner">Compañero: {partner}</div>

            <select
              className="position-select"
              value={myPos}
              onChange={(e) => setMyPos(e.target.value)}
            >
              <option value="0">0 · Mano</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3 · Postre</option>
            </select>
          </aside>

          <main className="felt-board">
            <section className="cards-row">
              <div className="row-title">Cartas del compañero</div>
              <div className="cards-grid">
                {partnerCards.map((card, idx) => (
                  <CardPicker
                    key={`partner-${idx}`}
                    label={`Carta ${idx + 1}`}
                    value={card}
                    onChange={(value) => {
                      const next = [...partnerCards];
                      next[idx] = value;
                      setPartnerCards(next);
                    }}
                  />
                ))}
              </div>
            </section>

            <section className="cards-row">
              <div className="row-title">Tus cartas</div>
              <div className="cards-grid">
                {myCards.map((card, idx) => (
                  <CardPicker
                    key={`my-${idx}`}
                    label={`Carta ${idx + 1}`}
                    value={card}
                    onChange={(value) => {
                      const next = [...myCards];
                      next[idx] = value;
                      setMyCards(next);
                    }}
                  />
                ))}
              </div>
            </section>
          </main>
        </section>

        {error ? <div className="error-box">{error}</div> : null}

        <section className="results">
          <MetricBox title="Grande" value={result ? pct(result.p_grande_win) : "—"} />
          <MetricBox title="Chica" value={result ? pct(result.p_chica_win) : "—"} />
          <MetricBox title="Llegar a pares" value={result ? pct(result.p_pares_reached) : "—"} />
          <MetricBox title="Ganar pares" value={result ? pct(result.p_pares_win) : "—"} />
          <MetricBox title="Llegar a juego" value={result ? pct(result.p_juego_reached) : "—"} />
          <MetricBox title="Ganar juego | juego" value={result ? pct(result.p_juego_win_given_reached) : "—"} />
          <MetricBox title="Ganar juego" value={result ? pct(result.p_juego_win) : "—"} />
          <MetricBox title="Llegar a punto" value={result ? pct(result.p_punto_reached) : "—"} />
          <MetricBox title="Ganar punto | punto" value={result ? pct(result.p_punto_win_given_reached) : "—"} />
          <MetricBox title="Ganar punto" value={result ? pct(result.p_punto_win) : "—"} />
        </section>
      </div>
    </div>
  );
}
