import Link from "next/link";
import { apiFetch, Offer } from "@/lib/api";

export default async function HomePage() {
  let offers: Offer[] = [];
  let unavailable = false;
  try {
    offers = await apiFetch<Offer[]>("/offers");
  } catch {
    unavailable = true;
  }

  return (
    <main>
      <section className="hero">
        <span className="pill">Picked by people you trust</span>
        <h1>Discover what creators actually choose.</h1>
        <p>Products, services and experiences curated by creators, with one place to discover the picks worth trying.</p>
        <div className="actions" style={{marginTop: 24}}>
          <a href="#discover" className="btn primary">Explore picks</a>
          <Link href="/login" className="btn">Creator or provider login</Link>
        </div>
      </section>

      <section className="section" id="discover">
        <h2>Discover offers</h2>
        {unavailable && <p className="muted">API is not available yet. Start the backend to load live offers.</p>}
        {!unavailable && offers.length === 0 && <p className="muted">No live offers yet.</p>}
        <div className="grid">
          {offers.map((offer) => (
            <article className="card" key={offer.id}>
              <span className="pill">{offer.offer_type}</span>
              <h3>{offer.title}</h3>
              <p className="muted">{offer.description ?? "A new PickByMe offer."}</p>
              <div className="price">{offer.price ? `${offer.price} ${offer.currency}` : "Price on request"}</div>
              <p className="muted">Creator commission up to {offer.default_creator_rate}%</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
