import { apiFetch } from "@/lib/api";

type CreatorPage = {
  creator_id: string;
  slug: string;
  display_name: string;
  bio: string | null;
  offers: Array<{
    id: string;
    title: string;
    description: string | null;
    offer_type: string;
    price: string | null;
    currency: string;
    is_featured: boolean;
    tracking_code: string;
  }>;
};

export default async function CreatorStorefront({ params }: { params: Promise<{slug: string}> }) {
  const { slug } = await params;
  const creator = await apiFetch<CreatorPage>(`/creators/${slug}`);

  return (
    <main>
      <section className="creator-head">
        <span className="pill">@{creator.slug}</span>
        <h1>{creator.display_name}</h1>
        <p className="muted">{creator.bio ?? "My PickByMe recommendations."}</p>
      </section>
      <section className="grid">
        {creator.offers.map((offer) => (
          <article className="card" key={offer.id}>
            {offer.is_featured && <span className="pill">Featured pick</span>}
            <h3>{offer.title}</h3>
            <p className="muted">{offer.description}</p>
            <div className="price">{offer.price ? `${offer.price} ${offer.currency}` : "Price on request"}</div>
            <p className="muted">Pick code: {offer.tracking_code}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
