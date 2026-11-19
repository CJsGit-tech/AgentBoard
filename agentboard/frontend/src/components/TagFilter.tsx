import { useId } from "react";

export function TagFilter({
  title,
  tags,
  selected,
  onChange,
}: {
  title: string;
  tags: string[];
  selected: string[];
  onChange: (tags: string[]) => void;
}) {
  const id = useId();
  const label = selected.length ? selected.join(", ") : `All ${title.toLowerCase()}`;

  return (
    <div className="tag-filter-control">
      <span className="filter-label">{title}</span>
    <details className="tag-filter-widget">
      <summary aria-label={`${title} filter. ${label}. Choose one or more values.`}>
        <span>{label}</span>
      </summary>
      <fieldset aria-label={title}>
        <legend>Select one or more {title.toLowerCase()}</legend>
        {tags.length ? tags.map((tag, index) => (
          <label key={tag} htmlFor={`${id}-${index}`}>
            <input
              id={`${id}-${index}`}
              type="checkbox"
              checked={selected.includes(tag)}
              onChange={(event) => onChange(event.target.checked
                ? [...selected, tag]
                : selected.filter((value) => value !== tag))}
            />
            <span>{tag}</span>
          </label>
        )) : <p className="muted small">No tags are available in this project.</p>}
        {selected.length > 0 && <button type="button" className="text-button" onClick={() => onChange([])}>Clear {title.toLowerCase()}</button>}
      </fieldset>
    </details>
    </div>
  );
}
