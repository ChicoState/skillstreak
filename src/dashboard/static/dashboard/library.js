(() => {
  "use strict";

  const browser = document.querySelector("[data-library-browser]");
  const form = document.querySelector("[data-library-search]");
  if (!browser || !form) {
    return;
  }

  const input = form.querySelector("input[name='q']");
  const tagSelect = form.querySelector("[data-library-tag]");
  const clearButton = form.querySelector("[data-library-clear]");
  const status = form.querySelector("[data-library-status]");
  const emptyState = document.querySelector("[data-library-empty]");
  const queryInputs = browser.querySelectorAll("[data-library-query]");
  const tagInputs = browser.querySelectorAll("[data-library-tag-input]");
  const items = [...browser.querySelectorAll("[data-library-item]")];

  const normalize = (value) => value.toLocaleLowerCase().trim();

  function updateAddressBar(query, tag) {
    const parameters = new URLSearchParams(window.location.search);
    if (query) {
      parameters.set("q", query);
    } else {
      parameters.delete("q");
    }
    if (tag) {
      parameters.set("tag", tag);
    } else {
      parameters.delete("tag");
    }
    const search = parameters.toString();
    window.history.replaceState({}, "", `${window.location.pathname}${search ? `?${search}` : ""}`);
  }

  function applyFilter({ updateUrl = false } = {}) {
    const queryValue = input.value.trim();
    const query = normalize(queryValue);
    const tag = tagSelect.value;
    let visibleCount = 0;

    queryInputs.forEach((queryInput) => {
      queryInput.value = queryValue;
    });
    tagInputs.forEach((tagInput) => {
      tagInput.value = tag;
    });
    clearButton.hidden = !query && !tag;

    items.forEach((item) => {
      const searchText = item.querySelector("[data-library-search-text]").textContent;
      const tagMatches = !tag || item.dataset.libraryTags.split(" ").includes(tag);
      const matches = tagMatches && (!query || normalize(searchText).includes(query));
      item.hidden = !matches;
      if (matches) {
        visibleCount += 1;
      }
    });

    emptyState.hidden = visibleCount !== 0;
    status.textContent = query
      ? `${visibleCount} skill${visibleCount === 1 ? "" : "s"} found for “${queryValue}”.`
      : tag
        ? `${visibleCount} skill${visibleCount === 1 ? "" : "s"} found.`
      : `${items.length} skill${items.length === 1 ? "" : "s"} available.`;
    if (updateUrl) {
      updateAddressBar(queryValue, tag);
    }
  }

  input.addEventListener("input", () => applyFilter({ updateUrl: true }));
  tagSelect.addEventListener("change", () => applyFilter({ updateUrl: true }));
  clearButton.addEventListener("click", () => {
    input.value = "";
    tagSelect.value = "";
    applyFilter({ updateUrl: true });
    input.focus();
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    applyFilter({ updateUrl: true });
  });

  applyFilter({ updateUrl: Boolean(input.value.trim() || tagSelect.value) });
})();
