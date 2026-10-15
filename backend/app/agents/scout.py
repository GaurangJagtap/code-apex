from urllib.parse import urljoin, urlparse
from typing import Dict, Any, List, Set
from playwright.async_api import Page
from backend.app.core.security import is_url_allowed

class ScoutAgent:
    """
    Scout Agent: Explores the application, extracts interactive DOM elements,
    identifies forms and controls, and discovers reachable application routes.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.discovered_urls: Set[str] = {base_url}
        self.navigation_graph: Dict[str, List[str]] = {}

    async def inspect_page(self, page: Page) -> Dict[str, Any]:
        """Inspects current page DOM, forms, links, and accessibility roles."""
        current_url = page.url
        title = await page.title()

        # Extract all interactive controls
        controls = await page.evaluate("""() => {
            const results = [];
            
            // Buttons
            document.querySelectorAll('button, [role="button"], input[type="submit"]').forEach(el => {
                if (el.offsetParent !== null) { // visible
                    results.push({
                        tag: el.tagName.toLowerCase(),
                        role: 'button',
                        id: el.id || null,
                        name: el.getAttribute('name') || null,
                        text: (el.innerText || el.value || '').trim().substring(0, 50),
                        selector: el.id ? '#' + el.id : (el.className ? '.' + el.className.split(' ')[0] : 'button')
                    });
                }
            });

            // Inputs
            document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]), select, textarea').forEach(el => {
                if (el.offsetParent !== null) {
                    results.push({
                        tag: el.tagName.toLowerCase(),
                        type: el.type || 'text',
                        role: 'input',
                        id: el.id || null,
                        name: el.getAttribute('name') || null,
                        placeholder: el.placeholder || null,
                        selector: el.id ? '#' + el.id : (el.name ? `[name="${el.name}"]` : el.tagName.toLowerCase())
                    });
                }
            });

            return results;
        }""")

        # Extract links
        raw_links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.getAttribute('href'))
                .filter(Boolean);
        }""")

        valid_links = []
        for raw in raw_links:
            if raw.startswith("javascript:") or raw.startswith("mailto:") or raw.startswith("#"):
                continue
            full_url = urljoin(current_url, raw)
            # Normalize url (remove query params or hash for site map clustering)
            parsed = urlparse(full_url)
            norm_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            if is_url_allowed(norm_url) and parsed.netloc == urlparse(self.base_url).netloc:
                valid_links.append(norm_url)
                if norm_url not in self.visited_urls:
                    self.discovered_urls.add(norm_url)

        self.visited_urls.add(current_url)
        self.navigation_graph[current_url] = list(set(valid_links))

        return {
            "url": current_url,
            "title": title,
            "controls": controls,
            "links": list(set(valid_links)),
            "unexplored_count": len(self.discovered_urls - self.visited_urls)
        }
