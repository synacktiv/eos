"""Info EOS plugin."""

from re import compile, IGNORECASE

from eos.plugins import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Info EOS plugin.

    Populate the Symfony instance with extracted info from the target deployment.
    - Symfony version
    - PHP version
    - Environment (prod, test, dev)
    """

    name = 'Info'
    priority = 50

    def run(self):
        """
        Get target versions.

        Perform a request to https://target.com/_profiler/<token>/?panel=config.
        Extract info from the response:
            <div class="metric">
                <span class="value">XXX</span>
                <span class="label">Symfony version</span>
            </div>
            <div class="metric">
                <span class="value">XXX</span>
                <span class="label">PHP version</span>
            </div>
        """

        # Perform request, and parse it
        r = self.symfony.profiler.get('latest', params={'panel': 'config'})
        soup = self.parse(r.text)

        # Version
        try:
            tag = None
            label = soup.find(string='Symfony version')
            if label:
                tag = label.find_previous('span', class_='value') or label.find_next('td')
            else:
                label = soup.find(string=compile('Based on', IGNORECASE))
                if label:
                    tag = label.find_next()
            self.symfony.version = tag.text.replace('Symfony', '').strip()
            self.log.warning('  Symfony %s', self.symfony.version)
        except:
            self.log.warning('Could not identify Symfony version')

        # PHP Version
        try:
            label = soup.find(string='PHP version')
            tag = label.find_previous('span', class_='value') or label.find_next('td')
            self.symfony.info['php_version'] = tag.text.replace(' ', '')
            self.log.warning('  PHP %s', self.symfony.info['php_version'])
        except:
            self.log.warning('Could not identify PHP version')

        # Environment
        try:
            label = soup.find(string='Environment')
            tag = label.find_previous('span', class_='value') or label.find_next('td')
            self.symfony.environment = tag.text
            self.log.warning('  Environment: %s', self.symfony.environment)
        except:
            self.log.warning('Could not identify Symfony environment')
