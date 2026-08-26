import { useEffect, useMemo, useState } from "react";
import { Button } from "react-aria-components/Button";
import { Dialog } from "react-aria-components/Dialog";
import { ListBox, ListBoxItem } from "react-aria-components/ListBox";
import { Modal, ModalOverlay } from "react-aria-components/Modal";
import { Input, Label, SearchField } from "react-aria-components/SearchField";

import { routes } from "../../navigation/routes";

type CommandPaletteProps = {
  activePath: string;
  isOpen: boolean;
  onNavigate: (path: string) => void;
  onOpenChange: (isOpen: boolean) => void;
  routeHref: (path: string) => string;
};

function isEditableTarget(target: EventTarget | null) {
  return target instanceof HTMLElement
    && (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));
}

function CommandPalette({ activePath, isOpen, onNavigate, onOpenChange, routeHref }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const matches = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (!normalized) return routes;
    return routes.filter((route) => (
      `${route.label} ${route.group} ${route.path} ${route.purpose}`.toLocaleLowerCase().includes(normalized)
    ));
  }, [query]);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      const commandShortcut = event.key.toLocaleLowerCase() === "k" && (event.ctrlKey || event.metaKey);
      const slashShortcut = event.key === "/"
        && !event.ctrlKey
        && !event.metaKey
        && !event.altKey
        && !event.shiftKey
        && !isEditableTarget(event.target)
        && !isEditableTarget(document.activeElement);

      if (!commandShortcut && !slashShortcut) return;
      event.preventDefault();
      onOpenChange(true);
    }

    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, [onOpenChange]);

  function chooseRoute(path: string) {
    onNavigate(routeHref(path));
    setQuery("");
    onOpenChange(false);
  }

  return (
    <ModalOverlay
      className="command-overlay"
      isDismissable
      isOpen={isOpen}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) setQuery("");
        onOpenChange(nextOpen);
      }}
    >
      <Modal className="command-modal">
        <Dialog aria-label="Navigate the Local AI Systems Lab" className="command-dialog">
          <div className="command-heading">
            <div>
              <p className="eyebrow">Keyboard navigation</p>
              <h2>Go to a workspace</h2>
            </div>
            <Button aria-label="Close command palette" className="command-close" slot="close">Esc</Button>
          </div>

          <SearchField className="command-search" value={query} onChange={setQuery}>
            <Label>Search workspaces</Label>
            <div>
              <span aria-hidden="true">⌕</span>
              <Input autoFocus placeholder="Try traces, hardware, or security…" />
              {query ? <Button aria-label="Clear search">Clear</Button> : null}
            </div>
          </SearchField>

          {matches.length ? (
            <ListBox
              aria-label="Matching workspaces"
              className="command-results"
              items={matches}
              onAction={(key) => chooseRoute(String(key))}
              selectionMode="none"
            >
              {(route) => (
                <ListBoxItem className="command-result" id={route.path} textValue={route.label}>
                  <span className="command-code" aria-hidden="true">{route.shortLabel}</span>
                  <span>
                    <strong>{route.label}</strong>
                    <small>{route.purpose}</small>
                  </span>
                  <span className="command-meta">
                    {route.path === activePath ? "Current" : route.group}
                  </span>
                </ListBoxItem>
              )}
            </ListBox>
          ) : (
            <p className="command-empty">No workspace matches “{query}”.</p>
          )}

          <footer className="command-footer">
            <span><kbd>↑</kbd><kbd>↓</kbd> Move</span>
            <span><kbd>Enter</kbd> Open</span>
            <span><kbd>Esc</kbd> Close</span>
          </footer>
        </Dialog>
      </Modal>
    </ModalOverlay>
  );
}

export { CommandPalette };
