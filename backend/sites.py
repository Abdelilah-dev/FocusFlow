import os
import re


class Sites:

    DOMAIN_PATTERN = re.compile(
        r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
        r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    )

    def __init__(self, initial_sites=None):
        if os.name == 'nt':
            base_dir = os.getenv('APPDATA') or os.path.expanduser('~')
        else:
            base_dir = os.path.expanduser('~')
            
        self.sites_path = os.path.join(base_dir, 'FocusFlow_Sites.txt')
        self.sites = self.load_sites()
        
        if initial_sites:
            for site in initial_sites:
                self.add_site(site)

    def clean_url(self, url: str) -> str:
        if not url or not isinstance(url, str):
            return ""
            
        clean = url.strip().lower()
        
        clean = re.sub(r'^https?://', '', clean)
        
        clean = clean.split('/')[0].split('?')[0].split('#')[0]
        
        clean = re.sub(r'^www\.', '', clean)
        
        if ':' in clean:
            clean = clean.split(':')[0]
            
        return clean.strip()

    def is_valid_domain(self, domain: str) -> bool:
        if not domain or len(domain) > 253:
            return False
        if domain == 'localhost':
            return True
        return bool(self.DOMAIN_PATTERN.match(domain))

    def load_sites(self) -> set:
        if not os.path.exists(self.sites_path):
            return set()
        
        try:
            with open(self.sites_path, 'r', encoding='utf-8') as f:
                return {
                    self.clean_url(line) 
                    for line in f 
                    if line.strip() and not line.strip().startswith('#')
                }
        except (OSError, IOError) as e:
            print(f"Error loading sites file: {e}")
            return set()

    def _save_sites(self):
        try:
            with open(self.sites_path, 'w', encoding='utf-8') as f:
                for site in sorted(self.sites):
                    f.write(site + '\n')
        except (OSError, IOError) as e:
            print(f"Error saving sites file: {e}")

    def add_site(self, site: str) -> bool:
        clean = self.clean_url(site)
        if clean and self.is_valid_domain(clean) and clean not in self.sites:
            self.sites.add(clean)
            self._save_sites()
            return True
        return False

    def remove_site(self, site: str) -> bool:
        clean = self.clean_url(site)
        if clean in self.sites:
            self.sites.remove(clean)
            self._save_sites()
            return True
        return False

    def get_all_sites(self) -> list:
        return sorted(self.sites)

    def clear_all(self):
        self.sites.clear()
        self._save_sites()

    def __contains__(self, site: str) -> bool:
        return self.clean_url(site) in self.sites

    def __len__(self) -> int:
        return len(self.sites)

    def __iter__(self):
        return iter(self.sites)