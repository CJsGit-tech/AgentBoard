import { Revision } from "../../api/types";
export function RevisionComparison({
  before,
  after,
}: {
  before: Revision;
  after: Revision;
}) {
  const a = before.content.split("\n"),
    b = after.content.split("\n");
  return (
    <section className="comparison-panel">
      <div className="section-heading">
        <div>
          <h2>
            Version {before.number} → Version {after.number}
          </h2>
          <p>Compare any two retained revisions</p>
        </div>
      </div>
      <div className="diff-columns">
        <section>
          <h3>Selected · version {before.number}</h3>
          {a.map((line, i) => (
            <div
              className={"diffline " + (!b.includes(line) ? "removed" : "")}
              key={i}
            >
              <span>{!b.includes(line) ? "−" : " "}</span>
              {line || " "}
            </div>
          ))}
        </section>
        <section>
          <h3>Compare with · version {after.number}</h3>
          {b.map((line, i) => (
            <div
              className={"diffline " + (!a.includes(line) ? "added" : "")}
              key={i}
            >
              <span>{!a.includes(line) ? "+" : " "}</span>
              {line || " "}
            </div>
          ))}
        </section>
      </div>
    </section>
  );
}
