import { useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "@mantine/core";
import { errorText, request, type Change, type Kind } from "../../model";

type ActivityPage = {
  items: Change[];
  next_before: string | null;
  facets: { actors: string[]; actions: string[]; kinds: Kind[] };
};
const blank: ActivityPage = { items: [], next_before: null, facets: { actors: [], actions: [], kinds: [] } };

export function useActivityPage(project: string | undefined, filters: Record<string, string>, version?: number) {
  const params = new URLSearchParams(Object.entries(filters).filter(([,value]) => value));
  const url = project ? 'projects/' + encodeURIComponent(project) + '/activity?' + params : '';
  const [retryCount, setRetryCount] = useState(0);
  const [result, setResult] = useState({ url: '', data: blank, busy: false, error: '' });
  const serial = useRef(0);
  const inFlight = useRef(false);
  useEffect(() => {
    const generation = ++serial.current;
    inFlight.current = false;
    if (!url) return;
    setResult(old => ({url, data: old.url === url ? old.data : blank, busy: true, error: ''}));
    request<ActivityPage>(url).then(data => {
      if (serial.current !== generation) return;
      setResult(old => {
        // Keep older pages already opened when fresh events arrive at the top.
        if (old.url === url && old.data.items.length > 0 && data.items.length > 0) {
          const lastFresh = data.items[data.items.length - 1].id;
          const overlap = old.data.items.findIndex(item => item.id === lastFresh);
          if (overlap >= 0 && overlap < old.data.items.length - 1) {
            return {url, data: {...data, items: [...data.items, ...old.data.items.slice(overlap + 1)],
              next_before: old.data.next_before}, busy: false, error: ''};
          }
        }
        return {url, data, busy: false, error: ''};
      });
    }).catch(e => {
      if (serial.current === generation) setResult(old => ({...old, busy: false, error: errorText(e)}));
    });
    return () => { ++serial.current; };
  }, [url, version, retryCount]);

  const data = result.url === url ? result.data : blank;
  async function loadMore() {
    if (!data.next_before || result.busy || inFlight.current) return;
    const generation = serial.current;
    inFlight.current = true;
    setResult(old => ({...old, busy: true, error: ''}));
    try {
      const page = await request<ActivityPage>(url + '&before=' + encodeURIComponent(data.next_before));
      if (generation === serial.current) setResult(old => ({
        url, data: {...page, items: [...old.data.items, ...page.items]}, busy: false, error: '',
      }));
    } catch (e) {
      if (generation === serial.current) setResult(old => ({...old, busy: false, error: errorText(e)}));
    } finally {
      if (generation === serial.current) inFlight.current = false;
    }
  }
  return {...data, busy: result.url !== url || result.busy, error: result.url === url ? result.error : '',
    loadMore, retry: () => setRetryCount(n => n + 1)};
}

export function ActivityPageContents({page, children}: {page: ReturnType<typeof useActivityPage>; children: ReactNode}) {
  return <>{page.error && <p role="alert">{page.error} <button className="link" onClick={page.retry}>Retry</button></p>}
    {page.busy && <p role="status">Loading history…</p>}
    {(page.items.length > 0 || (!page.busy && !page.error)) && children}
    {page.next_before && <Button variant="default" size="xs" disabled={page.busy} onClick={page.loadMore}>Load older changes</Button>}
  </>;
}
