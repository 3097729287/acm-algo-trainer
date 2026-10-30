// Calendar imports change public rows without a personal write. A distinct read
// avoids sharing an older in-flight catalogue response from before the import.
let readSerial = 0;
export function createCalendarCatalogReader({api, apply, currentOwner}) {
  let epoch = 0, sequence = 0, latest = null;
  const valid = ticket => ticket.epoch === epoch && ticket.owner === currentOwner() && ticket.isCurrent();
  function refresh(owner, {isCurrent = () => true} = {}) {
    if (!owner || owner !== currentOwner()) return Promise.resolve(false);
    const ticket = {owner, epoch, sequence: ++sequence, isCurrent};
    const newer = () => latest && latest.ticket.sequence > ticket.sequence && valid(latest.ticket);
    const promise = (async () => {
      try {
        const library = await api(`data?compact=1&calendar=${++readSerial}`);
        if (!valid(ticket)) return false;
        if (newer()) return latest.promise;
        apply(library, owner);
        return true;
      } catch (issue) {
        if (!valid(ticket)) return false;
        if (newer()) return latest.promise;
        throw issue;
      }
    })();
    latest = {ticket, promise};
    return promise;
  }
  return {refresh, invalidate() { epoch++; latest = null; }};
}
